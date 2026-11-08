// C# shim: F# cannot use the [JSExport] source generator, so the export lives here (same shape as Causa.Host).
using System.Runtime.InteropServices.JavaScript;
namespace Fixture.Host;
public static partial class Host
{
    static Fixture.App.Engine.Model model = Fixture.App.Engine.initial;
    [JSExport]
    public static string Dispatch(string evt) { model = Fixture.App.Engine.update(evt, model); return Fixture.App.Engine.project(model); }
    public static void Main() { }
}
