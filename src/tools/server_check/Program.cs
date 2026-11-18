// Loads a quests file (and optionally a locale file) with the SPT server's own code: its JsonUtil with its converters,
// into its models (Dictionary<MongoId, Quest>, Dictionary<string, string>), exactly as the server reads quests.json.
// Then it writes the quests back out with the server's settings and compares with the file (anything dropped or
// changed), and lists keys no server model has (the server keeps those in each model's ExtensionData but never reads
// them). Exit code 1 when a file doesn't load. With --json it prints one JSON object instead of text (what
// `python -m cli check --server` reads). Read-only: it never writes a file. See cli/DEVELOPING.md.
using System.Text.Json;
using System.Text.Json.Nodes;
using SPTarkov.Server.Core.Models.Common;
using SPTarkov.Server.Core.Models.Eft.Common.Tables;
using SPTarkov.Server.Core.Utils;
using SPTarkov.Server.Core.Utils.Json;

var asJson = args.Contains("--json");
var files = args.Where(a => !a.StartsWith("--")).ToArray();
if (files.Length < 1)
{
    Console.WriteLine("usage: server_check <quests.json> [locale.json] [--json]");
    return 2;
}

var report = new JsonObject { ["quests_file"] = files[0] };
var json = new JsonUtil(new IJsonConverterRegistrator[] { new SptJsonConverterRegistrator() });
var text = File.ReadAllText(files[0]);
Dictionary<MongoId, Quest>? quests;
try
{
    quests = json.Deserialize<Dictionary<MongoId, Quest>>(text);
}
catch (Exception e)
{
    return Finish(false, $"The server can't read the quests file: {e.GetType().Name}: {e.Message}");
}
report["quests"] = quests!.Count;
Say($"deserialized {quests.Count} quest(s) into Dictionary<MongoId, Quest>");

var original = JsonNode.Parse(text)!.AsObject();
var again = JsonNode.Parse(JsonSerializer.Serialize(quests, JsonUtil.JsonSerializerOptionsNoIndent))!.AsObject();
var dropped = new List<string>();
var changed = new List<string>();
var added = new List<string>();
Compare(original, again, "");
List("dropped", "keys the server drops", "  - ", dropped, 40);
List("changed", "values the server changes", "  ~ ", changed, 40);
List("added", "keys the server adds when writing", "  + ", added, 15);

// Keys no model property takes: the server keeps them in each model's injected ExtensionData (and writes them back),
// but no code reads them.
var unknown = new List<string>();
var seen = new HashSet<object>(ReferenceEqualityComparer.Instance);
foreach (var (id, quest) in quests) Walk(quest, $"{id}");
List("unknown", "keys no server model has (kept in ExtensionData, never read)", "  ? ", unknown, 40);

if (!asJson)
{
    foreach (var (id, quest) in quests)
    {
        var finish = quest.Conditions.AvailableForFinish ?? [];
        Console.WriteLine($"quest {id} '{quest.QuestName}': trader {quest.TraderId}, type {quest.Type}, location {quest.Location}, side {quest.Side}");
        foreach (var c in finish)
        {
            var steps = c.Counter?.Conditions?.Select(s => s.ConditionType) ?? [];
            Console.WriteLine($"  finish {c.ConditionType} {c.Id} value={c.Value} counter=[{string.Join(", ", steps)}] visibility={c.VisibilityConditions?.Count ?? 0}");
        }
        foreach (var r in quest.Rewards?.GetValueOrDefault("Success") ?? [])
        {
            Console.WriteLine($"  reward {r.Type} value={r.Value} items={r.Items?.Count ?? 0}");
        }
    }
}

if (files.Length > 1)
{
    report["locale_file"] = files[1];
    try
    {
        var locale = json.Deserialize<Dictionary<string, string>>(File.ReadAllText(files[1]));
        report["locale_entries"] = locale!.Count;
        Say($"locale: {locale.Count} entries read as Dictionary<string, string>");
    }
    catch (Exception e)
    {
        return Finish(false, $"The server can't read the locale file: {e.GetType().Name}: {e.Message}");
    }
}
return Finish(true, null);

int Finish(bool ok, string? error)
{
    report["ok"] = ok;
    if (error is not null)
    {
        report["error"] = error;
        if (!asJson) Console.WriteLine(error);
    }
    if (asJson) Console.WriteLine(report.ToJsonString());
    return ok ? 0 : 1;
}

void Say(string line)
{
    if (!asJson) Console.WriteLine(line);
}

void List(string key, string title, string mark, List<string> found, int shown)
{
    report[key] = new JsonArray(found.Select(f => (JsonNode)JsonValue.Create(f)!).ToArray());
    Say($"{title}: {found.Count}");
    foreach (var f in found.Take(shown)) Say(mark + f);
}

void Walk(object? node, string path)
{
    if (node is null || node is string || node.GetType().IsPrimitive || node.GetType().IsEnum || node is MongoId || !seen.Add(node)) return;
    if (node is System.Collections.IDictionary dict)
    {
        foreach (System.Collections.DictionaryEntry e in dict) Walk(e.Value, $"{path}.{e.Key}");
        return;
    }
    if (node is System.Collections.IEnumerable list)
    {
        var i = 0;
        foreach (var item in list) Walk(item, $"{path}[{i++}]");
        return;
    }
    var type = node.GetType();
    if (type.Namespace?.StartsWith("SPTarkov") != true) return;
    foreach (var p in type.GetProperties(System.Reflection.BindingFlags.Public | System.Reflection.BindingFlags.Instance))
    {
        if (p.GetIndexParameters().Length > 0) continue;
        var value = p.GetValue(node);
        if (p.Name == "ExtensionData" && value is IDictionary<string, object> extra)
        {
            foreach (var k in extra.Keys) unknown.Add($"{path}.{k}");
            continue;
        }
        Walk(value, $"{path}.{p.Name}");
    }
}

void Compare(JsonNode? a, JsonNode? b, string path)
{
    if (a is JsonObject oa)
    {
        if (b is not JsonObject ob)
        {
            changed.Add($"{path}: object became {b?.ToJsonString() ?? "null"}");
            return;
        }
        foreach (var (k, v) in oa)
        {
            if (!ob.ContainsKey(k))
            {
                if (v is not null) dropped.Add($"{path}.{k} = {Short(v)}");
            }
            else Compare(v, ob[k], $"{path}.{k}");
        }
        foreach (var (k, v) in ob)
        {
            if (!oa.ContainsKey(k)) added.Add($"{path}.{k} = {Short(v)}");
        }
        return;
    }
    if (a is JsonArray aa)
    {
        if (b is not JsonArray ab || aa.Count != ab.Count)
        {
            changed.Add($"{path}: {Short(a)} -> {Short(b)}");
            return;
        }
        for (var i = 0; i < aa.Count; i++) Compare(aa[i], ab[i], $"{path}[{i}]");
        return;
    }
    var sa = a?.ToJsonString();
    var sb = b?.ToJsonString();
    if (sa != sb && !(double.TryParse(sa, out var da) && double.TryParse(sb, out var db) && da == db))
    {
        changed.Add($"{path}: {sa} -> {sb}");
    }
}

static string Short(JsonNode? n)
{
    var s = n?.ToJsonString() ?? "null";
    return s.Length > 90 ? s[..90] + "..." : s;
}
