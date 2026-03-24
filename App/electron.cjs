const { app, BrowserWindow, ipcMain, dialog } = require("electron");
const path = require("path");
const { spawn } = require("child_process");
const isDev = require("electron-is-dev");
const http = require("http");

let mainWindow;
let pythonProcess = null;
const PORT = 5000;

function startPython() {
  let pythonExecutable, args, cwd;

  if (isDev) {

    pythonExecutable = "python";               
    args = [path.join(__dirname, "python", "server.py"), PORT];
    cwd = path.join(__dirname, "python");
  } else {

    pythonExecutable = path.join(
      process.resourcesPath,
      "python",
      "server.exe"         
    );
    args = [PORT];
    cwd = path.join(process.resourcesPath, "python");
  }

  pythonProcess = spawn(pythonExecutable, args, { cwd });
  pythonProcess.stdout.on("data", d => console.log("[Python]", d.toString()));
  pythonProcess.stderr.on("data", d => console.error("[Python ERR]", d.toString()));
}

function waitForServer(retries = 20) {
  return new Promise((resolve, reject) => {
    const attempt = () => {
      http.get(`http://127.0.0.1:${PORT}/health`, (res) => {
        if (res.statusCode === 200) return resolve();
        retry();
      }).on("error", retry);
    };
    const retry = () => {
      if (--retries <= 0) return reject(new Error("Python server never started"));
      setTimeout(attempt, 500);
    };
    attempt();
  });
}

async function createWindow() {

  startPython();

  // Wait up to 10 seconds for Flask to be ready
  try {
    await waitForServer();
    console.log("Python server is ready");
  } catch (e) {
    console.error(e.message);
  }
  mainWindow = new BrowserWindow({
    width: 800,
    height: 600,
    webPreferences: {
      nodeIntegration: true,
    },
  });

  const startURL = isDev
    ? "http://localhost:3000"
    : `file://${path.join(__dirname, "../build/index.html")}`;

  mainWindow.loadURL(startURL);

  mainWindow.on("closed", () => (mainWindow = null));
}

app.on("ready", createWindow);

app.on("window-all-closed", () => {
  if (process.platform !== "darwin") {
    app.quit();
  }
});

app.on("activate", () => {
  if (mainWindow === null) {
    createWindow();
  }
});

app.on("will-quit", () => pythonProcess?.kill());

ipcMain.handle("select-folder", async () => {
  const result = await dialog.showOpenDialog({
    properties: ["openDirectory"]
  });

  if (result.canceled) return null;

  return result.filePaths[0];
});

ipcMain.handle("select-excel-file", async () => {
  const result = await dialog.showOpenDialog({
    properties: ["openFile"],
    filters: [
      {
        name: "Excel Files",
        extensions: ["xlsx", "xls"]
      }
    ]
  });

  if (result.canceled) return null;

  return result.filePaths[0];
});

