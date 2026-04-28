const { app, BrowserWindow, ipcMain, dialog } = require("electron");
const path = require("path");
// const isDev = require("electron-is-dev");
const { spawn } = require("child_process");
const fs = require("fs");

let pythonProcess = null;
isDev = !app.isPackaged;

function createPythonProcess() {
  const script = isDev
    ? path.join(__dirname, "..", "calificacion-cartera", "src", "api.py")
    : path.join(process.resourcesPath, "api.exe");
  const pythonExecutable = path.join(
    __dirname,
    "..",
    ".venv",
    "Scripts",
    "python.exe",
  );
  console.log("Launching:", script);

  const exePath = path.join(process.resourcesPath, "api.exe");
  fs.writeFileSync(
    path.join(app.getPath("userData"), "debug.log"),
    `resourcesPath: ${process.resourcesPath}\nexe exists: ${fs.existsSync(exePath)}\npath: ${exePath}`,
  );

  pythonProcess = isDev
    ? spawn(pythonExecutable, [script])
    : spawn(script, [], { shell: true });
  //
  // pythonProcess.on("error", (err) => {
  //   fs.appendFileSync(
  //     path.join(app.getPath("userData"), "debug.log"),
  //     `\nSpawn error: ${err.message}`,
  //   );
  // });

  // pythonProcess.stderr.on("data", (data) => {
  //   fs.appendFileSync(
  //     path.join(app.getPath("userData"), "debug.log"),
  //     `\nStderr: ${data.toString()}`,
  //   );
  // });

  // pythonProcess.stdout.on("data", (data) => {
  //   fs.appendFileSync(
  //     path.join(app.getPath("userData"), "debug.log"),
  //     `\nStdout: ${data.toString()}`,
  //   );
  // });

  //
  pythonProcess.stdout.on("data", (data) => {
    console.log(`Python stdout: ${data}`);
  });

  pythonProcess.stderr.on("data", (data) => {
    console.error(`Python stderr: ${data}`);
  });

  pythonProcess.on("close", (code) => {
    console.log(`Python process exited with code ${code}`);
  });
}

let mainWindow;

function createWindow() {
  mainWindow = new BrowserWindow({
    width: 800,
    height: 600,
    webPreferences: {
      nodeIntegration: true,
      contextIsolation: false,
    },
  });

  const startURL = isDev
    ? "http://localhost:3000"
    : `file://${path.join(__dirname, "./build/index.html")}`;

  mainWindow.loadURL(startURL);

  mainWindow.on("closed", () => (mainWindow = null));
}

app.on("ready", () => {
  createPythonProcess();
  createWindow();
});

app.on("window-all-closed", () => {
  if (process.platform !== "darwin") {
    if (pythonProcess) {
      pythonProcess.kill();
    }
    app.quit();
  }
});

app.on("activate", () => {
  if (mainWindow === null) {
    createWindow();
  }
});

ipcMain.handle("select-folder", async () => {
  const result = await dialog.showOpenDialog({
    properties: ["openDirectory"],
  });

  if (result.canceled) return null;

  return result.filePaths[0];
});
