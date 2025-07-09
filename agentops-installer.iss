[Setup]
AppName=AgentOps Agent
AppVersion=1.0
DefaultDirName={pf}\AgentOps
DisableProgramGroupPage=yes

[Files]
Source: "dist\agentops-agent.exe"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{group}\AgentOps Agent"; Filename: "{app}\agentops-agent.exe"

[Registry]
Root: HKCU; Subkey: "Software\Microsoft\Windows\CurrentVersion\Run"; \
ValueName: "AgentOps Agent"; ValueType: string; \
ValueData: """{app}\agentops-agent.exe"""; Flags: uninsdeletevalue

[Run]
Filename: "{app}\agentops-agent.exe"; Description: "Launch AgentOps Agent"; Flags: nowait postinstall skipifsilent
