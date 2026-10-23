/// Entry point of a TestKit test assembly (compiled last; see Directory.Build.targets).
module TestKitProgram

[<EntryPoint>]
let main argv = Xunit.Runner.main (System.Reflection.Assembly.GetExecutingAssembly()) argv
