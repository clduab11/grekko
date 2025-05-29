// Phase 4.1: Electron Main Process Entry
// Implements ElectronApplicationManager per docs/phase4_ui_shell_pseudocode.md
import { app, BrowserWindow, ipcMain, Menu, globalShortcut } from 'electron';
import * as path from 'path';

// Type definitions (from pseudocode)
interface ApplicationConfig {
  windowConfig: WindowConfig;
  updateChannel: 'stable' | 'beta' | 'alpha';
  securityPolicy: SecurityPolicy;
  logging: LoggingConfig;
}
interface WindowConfig {
  width: number;
  height: number;
  maximized: boolean;
  fullscreen: boolean;
  alwaysOnTop: boolean;
}
interface SecurityPolicy {
  csp: ContentSecurityPolicy;
  nodeIntegration: boolean;
  contextIsolation: boolean;
  sandbox: boolean;
}
interface ContentSecurityPolicy {
  defaultSrc: string[];
  scriptSrc: string[];
  connectSrc: string[];
  imgSrc: string[];
}
interface LoggingConfig {
  level: string;
  file: string;
}

// --- ElectronApplicationManager ---
/**
 * Manages Electron app lifecycle, security, and main window.
 * All TDD anchors from pseudocode included as comments.
 */
class ElectronApplicationManager {
  private mainWindow: BrowserWindow | null = null;

  // TEST: Application initializes with correct configuration
  async initialize(config: ApplicationConfig): Promise<void> {
    this.validateConfig(config);
    this.setupSecurityPolicies(config.securityPolicy);
    this.setupAutoUpdater(config.updateChannel);
    this.registerGlobalShortcuts();
    this.setupApplicationMenu();
    this.setupIPCHandlers();
    this.createMainWindow(config.windowConfig);
  }

  // Validate configuration parameters
  private validateConfig(config: ApplicationConfig): void {
    if (!config || !config.windowConfig) {
      throw new Error('Invalid application configuration');
    }
    // Additional validation as needed
  }

  // TEST: Security policies prevent unauthorized access
  private setupSecurityPolicies(policy: SecurityPolicy): void {
    // Configure Content Security Policy
    // (CSP will be injected via headers or meta tag in production build)
    // See: https://www.electronjs.org/docs/latest/tutorial/security
    // Node integration and context isolation
    app.on('web-contents-created', (_event, contents) => {
      contents.session.webRequest.onHeadersReceived((_details, callback) => {
        callback({
          responseHeaders: {
            ..._details.responseHeaders,
            'Content-Security-Policy': [
              `default-src ${policy.csp.defaultSrc.join(' ')};` +
              `script-src ${policy.csp.scriptSrc.join(' ')};` +
              `connect-src ${policy.csp.connectSrc.join(' ')};` +
              `img-src ${policy.csp.imgSrc.join(' ')};`
            ]
          }
        });
      });
    });
    // Electron security flags are set per window in createMainWindow
  }

  // Configure auto-updater (stub for now)
  private setupAutoUpdater(_channel: string): void {
    // TDD anchor: setupAutoUpdater
    // Implement auto-update logic here (e.g., electron-updater)
  }

  // Register global shortcuts and menu
  private registerGlobalShortcuts(): void {
    // TDD anchor: registerGlobalShortcuts
    app.on('ready', () => {
      globalShortcut.register('CommandOrControl+Q', () => app.quit());
    });
  }

  private setupApplicationMenu(): void {
    // TDD anchor: setupApplicationMenu
    Menu.setApplicationMenu(Menu.buildFromTemplate([]));
  }

  // TEST: IPC handlers respond to renderer requests
  private setupIPCHandlers(): void {
    // TDD anchor: setupIPCHandlers
    // Example: ipcMain.handle('wallet:connect', ...)
  }

  // TEST: Main window creates with correct layout
  private createMainWindow(config: WindowConfig): void {
    this.mainWindow = new BrowserWindow({
      width: config.width || 1920,
      height: config.height || 1080,
      minWidth: 1200,
      minHeight: 800,
      webPreferences: {
        nodeIntegration: false,
        contextIsolation: true,
        enableRemoteModule: false,
        preload: path.join(__dirname, 'preload.js'),
        sandbox: true
      },
      titleBarStyle: 'hiddenInset',
      show: false
    });

    // Load renderer (to be implemented)
    this.mainWindow.loadFile('dist/index.html');

    this.mainWindow.once('ready-to-show', () => {
      this.mainWindow?.show();
      // TEST: Window appears in correct state
      if (config.maximized) {
        this.mainWindow?.maximize();
      }
    });
  }

  // TEST: Application shuts down gracefully
  async shutdown(): Promise<void> {
    BrowserWindow.getAllWindows().forEach(window => window.close());
    // cleanupResources(); // TDD anchor
    app.quit();
  }
}

// --- App Entry Point ---
const config: ApplicationConfig = {
  windowConfig: {
    width: Number(process.env.GREKKO_UI_WIDTH) || 1600,
    height: Number(process.env.GREKKO_UI_HEIGHT) || 900,
    maximized: !!process.env.GREKKO_UI_MAXIMIZED,
    fullscreen: !!process.env.GREKKO_UI_FULLSCREEN,
    alwaysOnTop: false
  },
  updateChannel: (process.env.GREKKO_UPDATE_CHANNEL as any) || 'stable',
  securityPolicy: {
    csp: {
      defaultSrc: ["'self'"],
      scriptSrc: ["'self'", "'unsafe-inline'"],
      connectSrc: ["'self'", "wss:", "https:"],
      imgSrc: ["'self'", "data:", "https:"]
    },
    nodeIntegration: false,
    contextIsolation: true,
    sandbox: true
  },
  logging: {
    level: process.env.GREKKO_LOG_LEVEL || 'info',
    file: process.env.GREKKO_LOG_FILE || 'grekko-ui.log'
  }
};

const appManager = new ElectronApplicationManager();

app.on('ready', async () => {
  try {
    await appManager.initialize(config);
  } catch (err) {
    // Error handling (to be expanded)
    console.error('Failed to initialize Electron app:', err);
    app.quit();
  }
});

app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') app.quit();
});

app.on('before-quit', async (e) => {
  e.preventDefault();
  await appManager.shutdown();
});