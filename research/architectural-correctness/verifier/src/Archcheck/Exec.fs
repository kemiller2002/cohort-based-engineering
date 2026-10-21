/// The only place the verifier starts processes. It runs `git` (read-only queries) and
/// `dotnet` (build and MSBuild evaluation); nothing from the evaluated repository is
/// executed directly.
module Archcheck.Exec

open System
open System.Diagnostics
open System.Text

type Outcome =
    { ExitCode: int
      Stdout: string
      Stderr: string }

/// Environment applied to every child `dotnet`: no telemetry, no first-run banner, no
/// persistent build servers (a lingering node would hold our redirected pipes open).
let private dotnetEnvironment =
    [ "DOTNET_CLI_TELEMETRY_OPTOUT", "1"
      "DOTNET_NOLOGO", "1"
      "DOTNET_SKIP_FIRST_TIME_EXPERIENCE", "1"
      "MSBUILDDISABLENODEREUSE", "1"
      "DOTNET_CLI_USE_MSBUILD_SERVER", "0"
      "UseSharedCompilation", "false" ]

let run (workingDirectory: string) (fileName: string) (args: string list) (timeout: TimeSpan) : Outcome =
    let psi = ProcessStartInfo(fileName)
    psi.WorkingDirectory <- workingDirectory
    psi.RedirectStandardOutput <- true
    psi.RedirectStandardError <- true
    psi.RedirectStandardInput <- true
    psi.UseShellExecute <- false
    psi.StandardOutputEncoding <- Encoding.UTF8
    psi.StandardErrorEncoding <- Encoding.UTF8
    args |> List.iter psi.ArgumentList.Add

    for k, v in dotnetEnvironment do
        psi.Environment[k] <- v

    // git must not page, prompt or read a global hook config that changes output.
    psi.Environment["GIT_TERMINAL_PROMPT"] <- "0"
    psi.Environment["GIT_PAGER"] <- "cat"

    use p = new Process(StartInfo = psi)
    let out = StringBuilder()
    let err = StringBuilder()
    p.OutputDataReceived.Add(fun e -> if not (isNull e.Data) then lock out (fun () -> out.AppendLine e.Data |> ignore))
    p.ErrorDataReceived.Add(fun e -> if not (isNull e.Data) then lock err (fun () -> err.AppendLine e.Data |> ignore))

    if not (p.Start()) then
        { ExitCode = -1; Stdout = ""; Stderr = $"could not start {fileName}" }
    else
        p.StandardInput.Close()
        p.BeginOutputReadLine()
        p.BeginErrorReadLine()

        if p.WaitForExit(int timeout.TotalMilliseconds) then
            p.WaitForExit()
            { ExitCode = p.ExitCode; Stdout = out.ToString(); Stderr = err.ToString() }
        else
            (try p.Kill true with _ -> ())
            { ExitCode = -1; Stdout = out.ToString(); Stderr = err.ToString() + $"\ntimed out after {timeout}" }

/// Raw bytes of a git command's stdout (for blobs and NUL-separated listings).
let runBytes (workingDirectory: string) (fileName: string) (args: string list) : int * byte[] =
    let psi = ProcessStartInfo(fileName)
    psi.WorkingDirectory <- workingDirectory
    psi.RedirectStandardOutput <- true
    psi.RedirectStandardError <- true
    psi.UseShellExecute <- false
    args |> List.iter psi.ArgumentList.Add
    psi.Environment["GIT_TERMINAL_PROMPT"] <- "0"
    use p = new Process(StartInfo = psi)
    p.Start() |> ignore
    let errTask = p.StandardError.ReadToEndAsync()
    use ms = new IO.MemoryStream()
    p.StandardOutput.BaseStream.CopyTo ms
    p.WaitForExit()
    errTask.Wait()
    p.ExitCode, ms.ToArray()

/// The `dotnet` host: the one running this process if it is `dotnet`, else from DOTNET_ROOT, else PATH.
let dotnetHost () =
    let current = Environment.ProcessPath

    if not (isNull current) && IO.Path.GetFileNameWithoutExtension(current) = "dotnet" then
        current
    else
        match Environment.GetEnvironmentVariable "DOTNET_ROOT" with
        | null
        | "" -> "dotnet"
        | root ->
            let candidate = IO.Path.Combine(root, "dotnet")
            if IO.File.Exists candidate then candidate else "dotnet"
