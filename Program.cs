using Microsoft.AspNetCore.Mvc;
using Microsoft.Data.Sqlite;
using SteamKit2;
using SteamKit2.GC;
using SteamKit2.GC.CSGO.Internal;
using SteamKit2.Internal;
using System.Collections.Concurrent;
using System.Text.Json;
using System.Text.Json.Serialization;
using System.Text.RegularExpressions;
using System.Web;
using CSGOSkinAPI.Services;
using CSGOSkinAPI.Models;

var builder = WebApplication.CreateBuilder(args);

builder.Services.AddControllers();
builder.Services.AddSingleton<SteamService>();
builder.Services.AddSingleton<DatabaseService>();
builder.Services.AddSingleton<ConstDataService>();

var app = builder.Build();

app.UseDefaultFiles(); // Must be before UseStaticFiles
app.UseStaticFiles();

app.UseRouting();
app.MapControllers();

// Initialize database on startup
var dbService = app.Services.GetRequiredService<DatabaseService>();
await dbService.InitializeDatabaseAsync();

// Initialize Steam connection
var steamService = app.Services.GetRequiredService<SteamService>();
_ = steamService.ConnectAsync();

// Initialize ConstDataService (loads const.json)
var constDataService = app.Services.GetRequiredService<ConstDataService>();

// Handle Ctrl-C gracefully
Console.CancelKeyPress += (sender, e) =>
{
    Console.WriteLine("\nReceived Ctrl-C, disconnecting from Steam...");
    steamService.Disconnect();
    e.Cancel = false;
};

app.Run();

namespace CSGOSkinAPI.Controllers
{
    [ApiController]
    [Route("api")]
    public partial class SkinController(SteamService steamService, DatabaseService dbService, ConstDataService constDataService) : ControllerBase
    {
        [GeneratedRegex(@"([SM])(\d+)A(\d+)D(\d+)", RegexOptions.Compiled)]
        private static partial Regex InspectUrlRegex();

        [HttpGet]
        public async Task<IActionResult> GetSkinData([FromQuery] string? url,
            [FromQuery] ulong s = 0, [FromQuery] ulong a = 0,
            [FromQuery] ulong d = 0, [FromQuery] ulong m = 0)
        {
            try
            {
                if (!string.IsNullOrEmpty(url))
                {
                    var parsed = ParseInspectUrl(url);
                    if (parsed == null)
                    {
                        Console.WriteLine("Failed to parse inspect URL");
                        return BadRequest(new { error = "Invalid inspect URL format" });
                    }

                    (s, a, d, m) = parsed.Value;
                }

                var existingItem = await dbService.GetItemAsync(a);
                if (existingItem != null)
                {
                    constDataService.FinalizeAttributes(existingItem);
                    return Ok(CreateResponse(existingItem));
                }

                var itemInfo = await steamService.GetItemInfoAsync(s, a, d, m);
                if (itemInfo == null)
                {
                    Console.WriteLine("Item not found in Steam GC");
                    return NotFound(new { error = "Item not found" });
                }

                await dbService.SaveItemAsync(itemInfo);
                constDataService.FinalizeAttributes(itemInfo);
                return Ok(CreateResponse(itemInfo));
            }
            catch (Exception ex)
            {
                Console.WriteLine($"Error in GetSkinData: {ex.Message}");
                return StatusCode(500, new { error = ex.Message });
            }
        }

        private static (ulong s, ulong a, ulong d, ulong m)? ParseInspectUrl(string url)
        {
            var decodedUrl = HttpUtility.UrlDecode(url);
            var match = InspectUrlRegex().Match(decodedUrl);
            if (!match.Success)
            {
                Console.WriteLine($"Failed to decode URL: {url}");
                return null;
            }

            ulong s = 0, a, d, m = 0;
            var firstParam = match.Groups[1].Value;
            var firstValue = ulong.Parse(match.Groups[2].Value);
            if (firstParam == "S")
            {
                s = firstValue;
            }
            else if (firstParam == "M")
            {
                m = firstValue;
            }
            a = ulong.Parse(match.Groups[3].Value);
            d = ulong.Parse(match.Groups[4].Value);
            return (s, a, d, m);
        }

        private static object CreateResponse(ItemInfo item)
        {
            return new
            {
                itemid = item.ItemId,
                defindex = item.DefIndex,
                paintindex = item.PaintIndex,
                rarity = item.Rarity,
                quality = item.Quality,
                paintwear = item.PaintWear,
                paintseed = item.PaintSeed,
                inventory = item.Inventory,
                origin = item.Origin,
                stattrak = item.StatTrak,
                special = item.Special,
                weapon = item.Weapon,
                skin = item.Skin
            };
        }
    }
}

namespace CSGOSkinAPI.Services
{
    public class SteamService
    {
        private readonly SteamClient _steamClient;
        private readonly SteamUser _steamUser;
        private readonly SteamGameCoordinator _steamGC;
        private readonly CallbackManager _manager;
        private bool _isConnected = false;
        private bool _isLoggedIn = false;
        private bool _isRunning = false;
        private readonly TaskCompletionSource<bool> _connectionTcs = new();
        private readonly ConcurrentDictionary<ulong, TaskCompletionSource<ItemInfo?>> _pendingRequests = new();

        private readonly string? _steamUsername = Environment.GetEnvironmentVariable("STEAM_USERNAME");
        private readonly string? _steamPassword = Environment.GetEnvironmentVariable("STEAM_PASSWORD");

        public SteamService()
        {
            _steamClient = new SteamClient();
            _steamUser = _steamClient.GetHandler<SteamUser>()!;
            _steamGC = _steamClient.GetHandler<SteamGameCoordinator>()!;
            _manager = new CallbackManager(_steamClient);

            _manager.Subscribe<SteamClient.ConnectedCallback>(OnConnected);
            _manager.Subscribe<SteamClient.DisconnectedCallback>(OnDisconnected);
            _manager.Subscribe<SteamUser.LoggedOnCallback>(OnLoggedOn);
            _manager.Subscribe<SteamUser.LoggedOffCallback>(OnLoggedOff);
            _manager.Subscribe<SteamGameCoordinator.MessageCallback>(OnGCMessage);
        }

        public async Task<ItemInfo?> GetItemInfoAsync(ulong s, ulong a, ulong d, ulong m)
        {
            if (!_isConnected)
            {
                Console.WriteLine("Not connected to Steam, connecting...");
                await ConnectAsync();
            }

            var jobId = a; // Use A (itemid) parameter as Job ID            
            if (_pendingRequests.ContainsKey(jobId))
            {
                Console.WriteLine($"Warning: JobID {jobId} already exists in pending requests");
                _pendingRequests.TryRemove(jobId, out _);
            }

            var tcs = new TaskCompletionSource<ItemInfo?>();
            _pendingRequests[jobId] = tcs;

            var request = new ClientGCMsgProtobuf<CMsgGCCStrike15_v2_Client2GCEconPreviewDataBlockRequest>(
                (uint)ECsgoGCMsg.k_EMsgGCCStrike15_v2_Client2GCEconPreviewDataBlockRequest);
            // request.SourceJobID = jobId;
            request.Body.param_s = s;
            request.Body.param_a = a;
            request.Body.param_d = d;
            request.Body.param_m = m;

            _steamGC.Send(request, 730);

            Console.WriteLine("Waiting for GC response...");
            var timeoutTask = Task.Delay(TimeSpan.FromSeconds(3));
            var completedTask = await Task.WhenAny(tcs.Task, timeoutTask);

            if (completedTask == timeoutTask)
            {
                Console.WriteLine($"GC request timed out for JobID: {jobId}");
                _pendingRequests.TryRemove(jobId, out _);
                tcs.SetResult(null);
            }

            return await tcs.Task;
        }

        public async Task ConnectAsync()
        {
            Console.WriteLine("ConnectAsync called - connecting to Steam");
            _steamClient.Connect();

            _isRunning = true;

            // Run callback manager in background continuously
            _ = Task.Run(() =>
            {
                Console.WriteLine("Starting callback manager loop");
                while (_isRunning)
                {
                    _manager.RunWaitCallbacks(TimeSpan.FromSeconds(1));
                }
                Console.WriteLine("Callback manager loop ended");
            });

            // Wait for connection and login
            var timeout = DateTime.UtcNow.AddSeconds(10);
            while ((!_isConnected || !_isLoggedIn) && DateTime.UtcNow < timeout)
            {
                Console.WriteLine("Waiting for login...");
                await Task.Delay(500);
            }

            if (!_isConnected || !_isLoggedIn)
            {
                throw new Exception("Failed to connect to Steam or login");
            }

            Console.WriteLine("Steam connection established");
        }

        public void Disconnect()
        {
            Console.WriteLine("Disconnecting from Steam...");
            _isRunning = false;
            _steamClient?.Disconnect();
        }

        private void OnConnected(SteamClient.ConnectedCallback callback)
        {
            Console.WriteLine("Steam client connected");
            _isConnected = true;

            if (!string.IsNullOrEmpty(_steamUsername) && !string.IsNullOrEmpty(_steamPassword))
            {
                Console.WriteLine($"Logging on with username: {_steamUsername}");
                _steamUser.LogOn(new SteamUser.LogOnDetails
                {
                    Username = _steamUsername,
                    Password = _steamPassword
                });
            }
            else
            {
                Console.WriteLine("No credentials provided, logging on anonymously");
                _steamUser.LogOnAnonymous();
            }
        }

        private void OnDisconnected(SteamClient.DisconnectedCallback callback)
        {
            Console.WriteLine($"Steam client disconnected. User initiated: {callback.UserInitiated}");
            _isConnected = false;
            _isLoggedIn = false;
        }

        private void OnLoggedOn(SteamUser.LoggedOnCallback callback)
        {
            Console.WriteLine($"Steam logon result: {callback.Result}");
            if (callback.Result != EResult.OK)
            {
                Console.WriteLine($"Failed to log on to Steam: {callback.Result}");
                return;
            }

            Console.WriteLine("Successfully logged on to Steam");
            _isLoggedIn = true;

            // Launch CS:GO to connect to game coordinator
            var playGame = new ClientMsgProtobuf<CMsgClientGamesPlayed>(EMsg.ClientGamesPlayed);
            playGame.Body.games_played.Add(new CMsgClientGamesPlayed.GamePlayed
            {
                game_id = new GameID(730)
            });
            _steamClient.Send(playGame);

            _ = Task.Run(async () =>
            {
                // Wait for CS:GO connection to stabilize before sending Hello
                Console.WriteLine("Waiting 5 seconds for connection to stabilize...");
                await Task.Delay(5000);

                // Send Hello message to GC to establish session
                Console.WriteLine("Sending Hello message to Game Coordinator...");
                var helloMsg = new ClientGCMsgProtobuf<SteamKit2.GC.CSGO.Internal.CMsgClientHello>((uint)EGCBaseClientMsg.k_EMsgGCClientHello);
                helloMsg.Body.version = 2000202; // Protocol version
                _steamGC.Send(helloMsg, 730);
            });

            _connectionTcs.SetResult(true);
        }

        private void OnLoggedOff(SteamUser.LoggedOffCallback callback)
        {
            Console.WriteLine($"Steam user logged off. Result: {callback.Result}");
            _isLoggedIn = false;
        }

        private void OnGCMessage(SteamGameCoordinator.MessageCallback callback)
        {
            if (callback.AppID != 730) return;

            if (callback.EMsg == (uint)ECsgoGCMsg.k_EMsgGCCStrike15_v2_Client2GCEconPreviewDataBlockResponse)
            {
                Console.WriteLine("=== GC Econ Preview Message Received ===");
                var response = new ClientGCMsgProtobuf<CMsgGCCStrike15_v2_Client2GCEconPreviewDataBlockResponse>(callback.Message);
                var responseItemId = response.Body.iteminfo?.itemid ?? 0;

                if (_pendingRequests.TryGetValue(responseItemId, out var pendingTcs))
                {
                    if (response.Body.iteminfo != null)
                    {
                        var itemInfo = response.Body.iteminfo;
                        var paintwear = BitConverter.ToSingle(BitConverter.GetBytes(itemInfo.paintwear), 0);
                        var item = new ItemInfo
                        {
                            ItemId = itemInfo.itemid,
                            DefIndex = (int)itemInfo.defindex,
                            PaintIndex = (int)itemInfo.paintindex,
                            Rarity = (int)itemInfo.rarity,
                            Quality = (int)itemInfo.quality,
                            PaintWear = paintwear,
                            PaintSeed = (int)itemInfo.paintseed,
                            Inventory = (long)itemInfo.inventory,
                            Origin = (int)itemInfo.origin,
                            StatTrak = itemInfo.ShouldSerializekilleatervalue()
                        };

                        pendingTcs.SetResult(item);
                    }
                    else
                    {
                        Console.WriteLine("No item info in response");
                        pendingTcs.SetResult(null);
                    }
                    _pendingRequests.TryRemove(responseItemId, out _);
                }
                else
                {
                    Console.WriteLine($"No pending request found for ItemID: {responseItemId}");
                }
            }
            else if (callback.EMsg == (uint)EGCBaseClientMsg.k_EMsgGCClientConnectionStatus)
            {
                var response = new ClientGCMsgProtobuf<CMsgConnectionStatus>(callback.Message);
                Console.WriteLine($"=== GC Connection Status ===");
                Console.WriteLine($"Status: {response.Body.status}");
                Console.WriteLine($"Client Session Need: {response.Body.client_session_need}");
                Console.WriteLine($"Queue Position: {response.Body.queue_position}");
                Console.WriteLine($"Wait Seconds: {response.Body.wait_seconds}");

                if (response.Body.status != GCConnectionStatus.GCConnectionStatus_HAVE_SESSION)
                {
                    Console.WriteLine("WARNING: Not properly connected to Game Coordinator!");
                }
            }
            else if (callback.EMsg == (uint)EGCBaseClientMsg.k_EMsgGCClientWelcome)
            {
                Console.WriteLine("=== GC Welcome Received ===");
                var response = new ClientGCMsgProtobuf<CMsgClientWelcome>(callback.Message);
                Console.WriteLine($"GC Version: {response.Body.version}");
            }
            else if (callback.EMsg == (uint)ECsgoGCMsg.k_EMsgGCCStrike15_v2_ClientLogonFatalError)
            {
                Console.WriteLine("=== GC Fatal Logon Error ===");
                var response = new ClientGCMsgProtobuf<CMsgGCCStrike15_v2_ClientLogonFatalError>(callback.Message);
                Console.WriteLine($"Code: {response.Body.errorcode}");
                Console.WriteLine($"Message: {response.Body.message}");
            }
            else if (callback.EMsg == (uint)ECsgoGCMsg.k_EMsgGCCStrike15_v2_GC2ClientGlobalStats)
            {
                Console.WriteLine("=== GC Global Stats Received ===");
                var response = new ClientGCMsgProtobuf<GlobalStatistics>(callback.Message);
                Console.WriteLine($"Players online: {response.Body.players_online}");
                Console.WriteLine($"Players searching: {response.Body.players_searching}");
                Console.WriteLine($"Servers online: {response.Body.servers_online}");
                Console.WriteLine($"Required AppID Version: {response.Body.required_appid_version2}");
            }
            else if (callback.EMsg == (uint)ECsgoGCMsg.k_EMsgGCCStrike15_v2_MatchmakingGC2ClientHello)
            {
                Console.WriteLine("=== GC Hello Received ===");
            }
            else if (callback.EMsg == (uint)ECsgoGCMsg.k_EMsgGCCStrike15_v2_ClientGCRankUpdate)
            {
                Console.WriteLine("=== GC Rank Update Received ===");
            }
            else
            {
                Console.WriteLine("=== Unhandled GC Message Received ===");
                Console.WriteLine($"Received GC message with EMsg: {callback.EMsg}");
            }
        }
    }

    public class DatabaseService
    {
        private const string ConnectionString = "Data Source=searches.db";

        public async Task InitializeDatabaseAsync()
        {
            using var connection = new SqliteConnection(ConnectionString);
            await connection.OpenAsync();

            var createTableCommand = @"
                CREATE TABLE IF NOT EXISTS searches (
                    itemid INTEGER PRIMARY KEY NOT NULL,
                    defindex INTEGER NOT NULL,
                    paintindex INTEGER NOT NULL,
                    rarity INTEGER NOT NULL,
                    quality INTEGER NOT NULL,
                    paintwear REAL NOT NULL,
                    paintseed INTEGER NOT NULL,
                    inventory INTEGER NOT NULL,
                    origin INTEGER NOT NULL,
                    stattrak INTEGER NOT NULL
                )";

            using var command = new SqliteCommand(createTableCommand, connection);
            await command.ExecuteNonQueryAsync();
        }

        public async Task<ItemInfo?> GetItemAsync(ulong itemId)
        {
            using var connection = new SqliteConnection(ConnectionString);
            await connection.OpenAsync();

            var query = "SELECT * FROM searches WHERE itemid = @itemid";
            using var command = new SqliteCommand(query, connection);
            command.Parameters.AddWithValue("@itemid", itemId);

            using var reader = await command.ExecuteReaderAsync();
            if (await reader.ReadAsync())
            {
                return new ItemInfo
                {
                    ItemId = (ulong)reader.GetInt64(reader.GetOrdinal("itemid")),
                    DefIndex = reader.GetInt32(reader.GetOrdinal("defindex")),
                    PaintIndex = reader.GetInt32(reader.GetOrdinal("paintindex")),
                    Rarity = reader.GetInt32(reader.GetOrdinal("rarity")),
                    Quality = reader.GetInt32(reader.GetOrdinal("quality")),
                    PaintWear = reader.GetDouble(reader.GetOrdinal("paintwear")),
                    PaintSeed = reader.GetInt32(reader.GetOrdinal("paintseed")),
                    Inventory = reader.GetInt64(reader.GetOrdinal("inventory")),
                    Origin = reader.GetInt32(reader.GetOrdinal("origin")),
                    StatTrak = reader.GetInt32(reader.GetOrdinal("stattrak")) == 1
                };
            }

            return null;
        }

        public async Task SaveItemAsync(ItemInfo item)
        {
            using var connection = new SqliteConnection(ConnectionString);
            await connection.OpenAsync();

            var insert = @"
                INSERT OR REPLACE INTO searches 
                (itemid, defindex, paintindex, rarity, quality, paintwear, paintseed, inventory, origin, stattrak)
                VALUES (@itemid, @defindex, @paintindex, @rarity, @quality, @paintwear, @paintseed, @inventory, @origin, @stattrak)";

            using var command = new SqliteCommand(insert, connection);
            command.Parameters.AddWithValue("@itemid", (long)item.ItemId);
            command.Parameters.AddWithValue("@defindex", item.DefIndex);
            command.Parameters.AddWithValue("@paintindex", item.PaintIndex);
            command.Parameters.AddWithValue("@rarity", item.Rarity);
            command.Parameters.AddWithValue("@quality", item.Quality);
            command.Parameters.AddWithValue("@paintwear", item.PaintWear);
            command.Parameters.AddWithValue("@paintseed", item.PaintSeed);
            command.Parameters.AddWithValue("@inventory", item.Inventory);
            command.Parameters.AddWithValue("@origin", item.Origin);
            command.Parameters.AddWithValue("@stattrak", item.StatTrak ? 1 : 0);

            await command.ExecuteNonQueryAsync();
        }
    }

    public class ConstDataService
    {
        private static readonly JsonSerializerOptions JsonOptions = new()
        {
            PropertyNameCaseInsensitive = true
        };

        private readonly ConstData _constData;

        public ConstDataService()
        {
            var jsonString = File.ReadAllText("const.json");
            _constData = JsonSerializer.Deserialize<ConstData>(jsonString, JsonOptions) ?? new ConstData();
        }

        public void FinalizeAttributes(ItemInfo item)
        {
            var weaponType = GetWeaponName(item.DefIndex);
            var pattern = GetPatternName(item.PaintIndex);
            var paintseed = item.PaintSeed;
            var paintindex = item.PaintIndex;

            item.Weapon = weaponType;
            item.Skin = pattern;

            var special = "";

            if (pattern == "Marble Fade" && _constData.Marbles?.ContainsKey(weaponType) == true)
            {
                if (_constData.Marbles[weaponType].TryGetValue(paintseed.ToString(), out var marbleType))
                {
                    special = marbleType;
                }
            }
            else if (pattern == "Fade" && _constData.Fades?.ContainsKey(weaponType) == true)
            {
                var fadeConfig = _constData.Fades[weaponType];
                var minimumFadePercent = fadeConfig.MinimumFadePercent;
                var orderReversed = fadeConfig.OrderReversed;

                var fadeIndex = _constData.FadeOrder != null ? Array.IndexOf(_constData.FadeOrder, paintseed) : -1;
                if (fadeIndex >= 0)
                {
                    if (orderReversed)
                    {
                        fadeIndex = 1000 - fadeIndex;
                    }
                    var actualFadePercent = (double)fadeIndex / 1001;
                    var scaledFadePercent = Math.Round(minimumFadePercent + actualFadePercent * (100 - minimumFadePercent), 1);
                    special = scaledFadePercent + "%";
                }
            }
            else if ((pattern == "Doppler" || pattern == "Gamma Doppler") && _constData.Doppler?.ContainsKey(paintindex.ToString()) == true)
            {
                special = _constData.Doppler[paintindex.ToString()];
            }
            else if (pattern == "Crimson Kimono" && _constData.Kimonos?.ContainsKey(paintseed.ToString()) == true)
            {
                special = _constData.Kimonos[paintseed.ToString()];
            }

            item.Special = special;
        }

        private string GetWeaponName(int defIndex)
        {
            if (_constData.Items?.TryGetValue(defIndex.ToString(), out var weapon) == true)
            {
                return weapon;
            }

            Console.WriteLine($"Item {defIndex} is missing from constants");
            return "";
        }

        private string GetPatternName(int paintIndex)
        {
            if (_constData.Skins?.TryGetValue(paintIndex.ToString(), out var pattern) == true)
            {
                return pattern;
            }

            Console.WriteLine($"Skin {paintIndex} is missing from constants");
            return "";
        }
    }
}

namespace CSGOSkinAPI.Models
{
    public class FadeConfigConverter : JsonConverter<FadeConfig>
    {
        public override FadeConfig Read(ref Utf8JsonReader reader, Type typeToConvert, JsonSerializerOptions options)
        {
            if (reader.TokenType != JsonTokenType.StartArray)
                throw new JsonException("Expected array for FadeConfig");

            using var document = JsonDocument.ParseValue(ref reader);
            var array = document.RootElement;

            if (array.GetArrayLength() != 2)
                throw new JsonException("FadeConfig array must have 2 elements");

            var minimumFadePercent = array[0].GetInt32();
            var orderReversed = array[1].GetBoolean();

            return new FadeConfig
            {
                MinimumFadePercent = minimumFadePercent,
                OrderReversed = orderReversed
            };
        }

        public override void Write(Utf8JsonWriter writer, FadeConfig value, JsonSerializerOptions options)
        {
            throw new NotSupportedException("Writing FadeConfig is not supported");
        }
    }

    [JsonConverter(typeof(FadeConfigConverter))]
    public class FadeConfig
    {
        public int MinimumFadePercent { get; set; }
        public bool OrderReversed { get; set; }
    }

    public class ConstData
    {
        public Dictionary<string, string>? Items { get; set; }
        public Dictionary<string, string>? Skins { get; set; }
        public Dictionary<string, FadeConfig>? Fades { get; set; }
        public Dictionary<string, Dictionary<string, string>>? Marbles { get; set; }
        public Dictionary<string, string>? Doppler { get; set; }
        public Dictionary<string, string>? Kimonos { get; set; }

        [JsonPropertyName("fade_order")]
        public int[]? FadeOrder { get; set; }
    }

    public class ItemInfo
    {
        public ulong ItemId { get; set; }
        public int DefIndex { get; set; }
        public int PaintIndex { get; set; }
        public int Rarity { get; set; }
        public int Quality { get; set; }
        public double PaintWear { get; set; }
        public int PaintSeed { get; set; }
        public long Inventory { get; set; }
        public int Origin { get; set; }
        public bool StatTrak { get; set; }
        public string? Special { get; set; }
        public string? Weapon { get; set; }
        public string? Skin { get; set; }
    }
}
