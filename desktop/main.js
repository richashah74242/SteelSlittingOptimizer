const {
  app,
  BrowserWindow
} = require("electron");

const path = require("path");
const { spawn } = require("child_process");

let backendProcess;

function startBackend() {
  const backendPath = path.join(
    process.resourcesPath,
    "backend",
    "steel-slitting-backend.exe"
  );

  backendProcess = spawn(
    backendPath,
    [],
    {
      windowsHide: true
    }
  );

  backendProcess.stdout.on(
    "data",
    (data) => {
      console.log(
        `Backend: ${data}`
      );
    }
  );

  backendProcess.stderr.on(
    "data",
    (data) => {
      console.log(
        `Backend Error: ${data}`
      );
    }
  );
}

function createWindow() {
  const window = new BrowserWindow({
    width: 1400,
    height: 900,
    webPreferences: {
      contextIsolation: true,
      nodeIntegration: false
    }
  });

  window.loadFile(
    path.join(
      __dirname,
      "../frontend/dist/index.html"
    )
  );
}

app.whenReady().then(() => {
  startBackend();

  setTimeout(() => {
    createWindow();
  }, 1500);
});

app.on(
  "window-all-closed",
  () => {
    if (backendProcess) {
      backendProcess.kill();
    }

    if (process.platform !== "darwin") {
      app.quit();
    }
  }
);