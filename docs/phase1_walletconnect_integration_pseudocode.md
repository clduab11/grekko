# Phase 1: WalletConnect Integration - Pseudocode Specification

## Overview

This document provides the pseudocode specification for WalletConnect v2 protocol integration, including QR code session establishment, mobile wallet communication, and multi-chain support for Phase 1 of the Grekko DeFi trading platform.

## Module: WalletConnectClient

```pseudocode
// WalletConnect v2 protocol integration client
CLASS WalletConnectClient IMPLEMENTS WalletProvider {
    PRIVATE client: WalletConnectClient
    PRIVATE config: WalletConnectConfig
    PRIVATE eventEmitter: EventEmitter
    PRIVATE logger: Logger
    PRIVATE sessionManager: SessionManager
    PRIVATE qrCodeGenerator: QRCodeGenerator
    PRIVATE connectionState: ConnectionState
    PRIVATE activeSessions: Map<String, Session>
    
    // Provider identity
    READONLY providerId = "walletconnect"
    READONLY name = "WalletConnect"
    READONLY version: String
    READONLY supportedChains: Array<ChainId>
    READONLY capabilities: Array<WalletCapability>
    
    // Connection state
    isAvailable: Boolean = true
    isConnected: Boolean = false
    
    // TEST: Should initialize with valid configuration
    // TEST: Should setup WalletConnect client correctly
    // TEST: Should validate required parameters
    CONSTRUCTOR(config: WalletConnectConfig) {
        this.config = this.validateConfig(config)
        this.eventEmitter = NEW EventEmitter()
        this.logger = NEW Logger("WalletConnectClient")
        this.sessionManager = NEW SessionManager()
        this.qrCodeGenerator = NEW QRCodeGenerator()
        this.connectionState = DISCONNECTED
        this.activeSessions = NEW Map()
        
        this.version = "2.0.0"
        this.supportedChains = config.supportedChains || [
            ETHEREUM, POLYGON, BSC, ARBITRUM, OPTIMISM, BASE
        ]
        this.capabilities = [
            SIGN_MESSAGE, SIGN_TRANSACTION, SEND_TRANSACTION,
            SWITCH_CHAIN, ADD_CHAIN
        ]
        
        this.initializeClient()
    }
    
    // TEST: Should initialize WalletConnect client successfully
    // TEST: Should setup event listeners correctly
    // TEST: Should handle initialization errors
    PRIVATE FUNCTION initializeClient(): Promise<Void> {
        TRY {
            this.client = AWAIT WalletConnectClient.init({
                projectId: this.config.projectId,
                metadata: this.config.metadata,
                relayUrl: this.config.relayUrl || "wss://relay.walletconnect.com"
            })
            
            this.setupClientEventListeners()
            this.restoreExistingSessions()
            
            this.logger.info("WalletConnect client initialized")
            
        } CATCH error {
            this.logger.error("WalletConnect initialization failed", error)
            this.isAvailable = false
        }
    }
    
    // TEST: Should generate QR code and establish session
    // TEST: Should handle session approval/rejection
    // TEST: Should timeout connection attempts
    // TEST: Should support multiple chain selection
    FUNCTION connect(options: ConnectionOptions = {}): Promise<WalletConnection> {
        IF NOT this.isAvailable {
            THROW NEW Error(PROVIDER_UNAVAILABLE)
        }
        
        // Check for existing active session
        existingSession = this.getActiveSession()
        IF existingSession {
            RETURN this.createWalletConnectionFromSession(existingSession)
        }
        
        this.connectionState = CONNECTING
        
        TRY {
            // Create connection proposal
            proposal = {
                requiredNamespaces: this.buildRequiredNamespaces(options),
                optionalNamespaces: this.buildOptionalNamespaces(options),
                sessionProperties: this.config.sessionProperties || {}
            }
            
            // Connect and get URI for QR code
            connectResult = AWAIT this.client.connect(proposal)
            uri = connectResult.uri
            
            // Generate QR code
            qrCode = AWAIT this.qrCodeGenerator.generate(uri)
            
            // Emit QR code event for UI display
            this.eventEmitter.emit("qrCodeGenerated", {
                uri: uri,
                qrCode: qrCode
            })
            
            this.logger.info("QR code generated for WalletConnect session")
            
            // Wait for session approval with timeout
            session = AWAIT Promise.race([
                connectResult.approval(),
                this.createTimeoutPromise(options.timeout || 300000) // 5 minutes
            ])
            
            // Store session
            this.activeSessions.set(session.topic, session)
            this.sessionManager.storeSession(session)
            
            // Update connection state
            this.isConnected = true
            this.connectionState = CONNECTED
            
            // Create wallet connection
            connection = this.createWalletConnectionFromSession(session)
            
            // Emit connection event
            this.eventEmitter.emit("connect", {
                connectionId: connection.connectionId,
                accounts: connection.accounts,
                chainId: connection.chainId,
                sessionTopic: session.topic
            })
            
            this.logger.info("WalletConnect session established", {
                topic: session.topic,
                accountCount: connection.accounts.length
            })
            
            RETURN connection
            
        } CATCH error {
            this.connectionState = ERROR
            this.logger.error("WalletConnect connection failed", error)
            
            IF error.message.includes("timeout") {
                THROW NEW Error(CONNECTION_TIMEOUT)
            } ELSE IF error.message.includes("rejected") {
                THROW NEW Error(USER_REJECTED_REQUEST)
            } ELSE {
                THROW NEW Error(CONNECTION_FAILED, error.message)
            }
        }
    }
    
    // TEST: Should disconnect active session
    // TEST: Should clean up session data
    // TEST: Should handle disconnection errors
    FUNCTION disconnect(): Promise<Void> {
        IF NOT this.isConnected {
            RETURN
        }
        
        this.connectionState = DISCONNECTING
        
        TRY {
            // Disconnect all active sessions
            disconnectionPromises = []
            FOR session IN this.activeSessions.values() {
                disconnectionPromises.push(this.disconnectSession(session))
            }
            
            AWAIT Promise.allSettled(disconnectionPromises)
            
            // Clear session storage
            this.activeSessions.clear()
            this.sessionManager.clearSessions()
            
            // Update connection state
            this.isConnected = false
            this.connectionState = DISCONNECTED
            
            // Emit disconnection event
            this.eventEmitter.emit("disconnect", {
                providerId: this.providerId
            })
            
            this.logger.info("WalletConnect disconnected")
            
        } CATCH error {
            this.logger.error("WalletConnect disconnection failed", error)
            THROW NEW Error(DISCONNECTION_FAILED, error.message)
        }
    }
    
    // TEST: Should return accounts from active session
    // TEST: Should handle multiple sessions
    // TEST: Should validate account format
    FUNCTION getAccounts(): Promise<Array<Account>> {
        IF NOT this.isConnected {
            THROW NEW Error(NOT_CONNECTED)
        }
        
        TRY {
            accounts = []
            
            FOR session IN this.activeSessions.values() {
                sessionAccounts = this.extractAccountsFromSession(session)
                FOR account IN sessionAccounts {
                    IF this.isValidAddress(account.address) {
                        balance = AWAIT this.getAccountBalance(account.address, account.chainId)
                        accounts.push({
                            address: account.address,
                            name: account.name || `Account ${accounts.length + 1}`,
                            balance: balance,
                            isActive: accounts.length === 0,
                            chainId: account.chainId
                        })
                    }
                }
            }
            
            RETURN accounts
            
        } CATCH error {
            this.logger.error("Failed to get accounts", error)
            THROW NEW Error(ACCOUNT_FETCH_FAILED, error.message)
        }
    }
    
    // TEST: Should successfully switch chain in session
    // TEST: Should handle unsupported chains
    // TEST: Should update session namespaces
    FUNCTION switchChain(chainId: ChainId): Promise<Void> {
        IF NOT this.supportedChains.includes(chainId) {
            THROW NEW Error(UNSUPPORTED_CHAIN)
        }
        
        activeSession = this.getActiveSession()
        IF NOT activeSession {
            THROW NEW Error(NO_ACTIVE_SESSION)
        }
        
        TRY {
            // Check if chain is already supported in session
            chainNamespace = this.getChainNamespace(chainId)
            IF NOT activeSession.namespaces[chainNamespace] {
                // Request to add chain to session
                AWAIT this.requestChainPermission(activeSession, chainId)
            }
            
            // Emit chain changed event
            this.eventEmitter.emit("chainChanged", {
                chainId: chainId,
                providerId: this.providerId,
                sessionTopic: activeSession.topic
            })
            
            this.logger.info("Chain switched", { chainId, sessionTopic: activeSession.topic })
            
        } CATCH error {
            this.logger.error("Chain switch failed", error)
            THROW NEW Error(CHAIN_SWITCH_FAILED, error.message)
        }
    }
    
    // TEST: Should successfully sign message
    // TEST: Should use correct signing method
    // TEST: Should handle user rejection
    FUNCTION signMessage(message: String, method: String = "personal_sign"): Promise<String> {
        IF NOT this.isConnected {
            THROW NEW Error(NOT_CONNECTED)
        }
        
        // Validate message
        IF message IS EMPTY OR message.length > 2000 {
            THROW NEW Error(INVALID_MESSAGE)
        }
        
        activeSession = this.getActiveSession()
        IF NOT activeSession {
            THROW NEW Error(NO_ACTIVE_SESSION)
        }
        
        TRY {
            // Get active account
            activeAccount = this.getActiveAccount(activeSession)
            IF NOT activeAccount {
                THROW NEW Error(NO_ACTIVE_ACCOUNT)
            }
            
            // Prepare signing request
            request = {
                topic: activeSession.topic,
                chainId: this.formatChainId(activeAccount.chainId),
                request: {
                    method: method,
                    params: method === "personal_sign" ? 
                        [this.toHex(message), activeAccount.address] :
                        [activeAccount.address, message]
                }
            }
            
            // Send signing request
            signature = AWAIT this.client.request(request)
            
            this.logger.info("Message signed via WalletConnect", {
                method: method,
                account: activeAccount.address,
                sessionTopic: activeSession.topic
            })
            
            RETURN signature
            
        } CATCH error {
            IF error.message.includes("rejected") {
                THROW NEW Error(USER_REJECTED_REQUEST)
            } ELSE {
                this.logger.error("Message signing failed", error)
                THROW NEW Error(SIGNING_FAILED, error.message)
            }
        }
    }
    
    // TEST: Should successfully sign transaction
    // TEST: Should validate transaction parameters
    // TEST: Should handle different transaction types
    FUNCTION signTransaction(transaction: TransactionRequest): Promise<SignedTransaction> {
        IF NOT this.isConnected {
            THROW NEW Error(NOT_CONNECTED)
        }
        
        activeSession = this.getActiveSession()
        IF NOT activeSession {
            THROW NEW Error(NO_ACTIVE_SESSION)
        }
        
        // Validate and prepare transaction
        validatedTx = this.validateTransaction(transaction)
        
        TRY {
            // Get active account
            activeAccount = this.getActiveAccount(activeSession)
            IF NOT activeAccount {
                THROW NEW Error(NO_ACTIVE_ACCOUNT)
            }
            
            // Prepare transaction for signing
            txForSigning = this.prepareTransactionForSigning(validatedTx, activeAccount)
            
            // Send signing request
            request = {
                topic: activeSession.topic,
                chainId: this.formatChainId(activeAccount.chainId),
                request: {
                    method: "eth_signTransaction",
                    params: [txForSigning]
                }
            }
            
            signedTxData = AWAIT this.client.request(request)
            
            signedTransaction = {
                raw: signedTxData,
                tx: txForSigning,
                hash: this.calculateTransactionHash(signedTxData)
            }
            
            this.logger.info("Transaction signed via WalletConnect", {
                to: txForSigning.to,
                value: txForSigning.value,
                sessionTopic: activeSession.topic
            })
            
            RETURN signedTransaction
            
        } CATCH error {
            IF error.message.includes("rejected") {
                THROW NEW Error(USER_REJECTED_REQUEST)
            } ELSE {
                this.logger.error("Transaction signing failed", error)
                THROW NEW Error(SIGNING_FAILED, error.message)
            }
        }
    }
    
    // TEST: Should successfully send transaction
    // TEST: Should monitor transaction status
    // TEST: Should handle network errors
    FUNCTION sendTransaction(transaction: TransactionRequest): Promise<TransactionHash> {
        IF NOT this.isConnected {
            THROW NEW Error(NOT_CONNECTED)
        }
        
        activeSession = this.getActiveSession()
        IF NOT activeSession {
            THROW NEW Error(NO_ACTIVE_SESSION)
        }
        
        // Validate and prepare transaction
        validatedTx = this.validateTransaction(transaction)
        
        TRY {
            // Get active account
            activeAccount = this.getActiveAccount(activeSession)
            IF NOT activeAccount {
                THROW NEW Error(NO_ACTIVE_ACCOUNT)
            }
            
            // Prepare transaction for sending
            txForSending = this.prepareTransactionForSending(validatedTx, activeAccount)
            
            // Send transaction request
            request = {
                topic: activeSession.topic,
                chainId: this.formatChainId(activeAccount.chainId),
                request: {
                    method: "eth_sendTransaction",
                    params: [txForSending]
                }
            }
            
            txHash = AWAIT this.client.request(request)
            
            // Start monitoring transaction
            this.monitorTransaction(txHash, activeAccount.chainId)
            
            this.logger.info("Transaction sent via WalletConnect", {
                hash: txHash,
                to: txForSending.to,
                sessionTopic: activeSession.topic
            })
            
            RETURN txHash
            
        } CATCH error {
            IF error.message.includes("rejected") {
                THROW NEW Error(USER_REJECTED_REQUEST)
            } ELSE {
                this.logger.error("Transaction send failed", error)
                THROW NEW Error(SEND_FAILED, error.message)
            }
        }
    }
    
    // TEST: Should setup client event listeners correctly
    // TEST: Should handle session proposal events
    // TEST: Should handle session delete events
    PRIVATE FUNCTION setupClientEventListeners(): Void {
        // Session proposal event
        this.client.on("session_proposal", (proposal) => {
            this.handleSessionProposal(proposal)
        })
        
        // Session request event
        this.client.on("session_request", (request) => {
            this.handleSessionRequest(request)
        })
        
        // Session delete event
        this.client.on("session_delete", (session) => {
            this.handleSessionDelete(session)
        })
        
        // Session update event
        this.client.on("session_update", (session) => {
            this.handleSessionUpdate(session)
        })
        
        // Session extend event
        this.client.on("session_extend", (session) => {
            this.handleSessionExtend(session)
        })
        
        this.logger.info("WalletConnect client event listeners setup")
    }
    
    // TEST: Should build required namespaces correctly
    // TEST: Should include all supported chains
    // TEST: Should specify required methods and events
    PRIVATE FUNCTION buildRequiredNamespaces(options: ConnectionOptions): Object {
        namespaces = {}
        
        // Build EIP155 namespace for Ethereum-compatible chains
        eip155Chains = this.supportedChains
            .filter(chainId => this.isEIP155Chain(chainId))
            .map(chainId => this.formatChainId(chainId))
        
        IF eip155Chains.length > 0 {
            namespaces.eip155 = {
                chains: eip155Chains,
                methods: [
                    "eth_sendTransaction",
                    "eth_signTransaction", 
                    "eth_sign",
                    "personal_sign",
                    "eth_signTypedData",
                    "eth_signTypedData_v4"
                ],
                events: [
                    "chainChanged",
                    "accountsChanged"
                ]
            }
        }
        
        // Add other namespaces if needed (Solana, etc.)
        
        RETURN namespaces
    }
    
    // TEST: Should build optional namespaces correctly
    // TEST: Should include additional methods and events
    PRIVATE FUNCTION buildOptionalNamespaces(options: ConnectionOptions): Object {
        namespaces = {}
        
        // Optional EIP155 methods
        namespaces.eip155 = {
            chains: this.supportedChains
                .filter(chainId => this.isEIP155Chain(chainId))
                .map(chainId => this.formatChainId(chainId)),
            methods: [
                "eth_accounts",
                "eth_requestAccounts",
                "eth_getBalance",
                "eth_chainId",
                "wallet_switchEthereumChain",
                "wallet_addEthereumChain",
                "wallet_watchAsset"
            ],
            events: [
                "connect",
                "disconnect"
            ]
        }
        
        RETURN namespaces
    }
    
    // TEST: Should restore existing sessions on initialization
    // TEST: Should validate session expiry
    // TEST: Should clean up expired sessions
    PRIVATE FUNCTION restoreExistingSessions(): Void {
        TRY {
            storedSessions = this.sessionManager.getStoredSessions()
            
            FOR session IN storedSessions {
                // Check if session is still valid
                IF this.isSessionValid(session) {
                    this.activeSessions.set(session.topic, session)
                    this.isConnected = true
                    this.connectionState = CONNECTED
                    
                    this.logger.info("Restored WalletConnect session", {
                        topic: session.topic
                    })
                } ELSE {
                    // Clean up expired session
                    this.sessionManager.removeSession(session.topic)
                    this.logger.info("Removed expired session", {
                        topic: session.topic
                    })
                }
            }
            
        } CATCH error {
            this.logger.error("Failed to restore sessions", error)
        }
    }
    
    // TEST: Should validate session expiry correctly
    // TEST: Should check session connectivity
    PRIVATE FUNCTION isSessionValid(session: Session): Boolean {
        // Check expiry
        IF session.expiry * 1000 < Date.now() {
            RETURN false
        }
        
        // Check if session is acknowledged
        IF NOT session.acknowledged {
            RETURN false
        }
        
        // Additional validation checks
        IF NOT session.namespaces OR Object.keys(session.namespaces).length === 0 {
            RETURN false
        }
        
        RETURN true
    }
    
    // TEST: Should get active session correctly
    // TEST: Should return most recent session when multiple exist
    PRIVATE FUNCTION getActiveSession(): Session? {
        IF this.activeSessions.size === 0 {
            RETURN NULL
        }
        
        // Return the most recently created session
        sessions = Array.from(this.activeSessions.values())
        RETURN sessions.sort((a, b) => b.expiry - a.expiry)[0]
    }
    
    // TEST: Should extract accounts from session correctly
    // TEST: Should handle multiple namespaces
    PRIVATE FUNCTION extractAccountsFromSession(session: Session): Array<SessionAccount> {
        accounts = []
        
        FOR namespace IN Object.keys(session.namespaces) {
            namespaceData = session.namespaces[namespace]
            
            FOR account IN namespaceData.accounts {
                parsedAccount = this.parseAccount(account)
                IF parsedAccount {
                    accounts.push(parsedAccount)
                }
            }
        }
        
        RETURN accounts
    }
    
    // TEST: Should parse account string correctly
    // TEST: Should extract chain ID and address
    PRIVATE FUNCTION parseAccount(accountString: String): SessionAccount? {
        // Format: "eip155:1:0x1234..."
        parts = accountString.split(":")
        
        IF parts.length !== 3 {
            RETURN NULL
        }
        
        namespace = parts[0]
        chainId = parseInt(parts[1])
        address = parts[2]
        
        IF NOT this.isValidAddress(address) {
            RETURN NULL
        }
        
        RETURN {
            namespace: namespace,
            chainId: chainId,
            address: address
        }
    }
    
    // Event handling methods
    FUNCTION addEventListener(event: WalletEvent, handler: EventHandler): Void {
        this.eventEmitter.on(event, handler)
    }
    
    FUNCTION removeEventListener(event: WalletEvent, handler: EventHandler): Void {
        this.eventEmitter.off(event, handler)
    }
    
    FUNCTION emit(event: WalletEvent, data: Any): Void {
        this.eventEmitter.emit(event, data)
    }
}
```

## Module: SessionManager

```pseudocode
// Manages WalletConnect session persistence and recovery
CLASS SessionManager {
    PRIVATE storage: Storage
    PRIVATE logger: Logger
    PRIVATE sessionKey: String = "walletconnect_sessions"
    
    // TEST: Should initialize with storage backend
    CONSTRUCTOR(storage: Storage = localStorage) {
        this.storage = storage
        this.logger = NEW Logger("SessionManager")
    }
    
    // TEST: Should store session correctly
    // TEST: Should encrypt sensitive session data
    FUNCTION storeSession(session: Session): Void {
        TRY {
            sessions = this.getStoredSessions()
            sessions[session.topic] = this.sanitizeSession(session)
            
            this.storage.setItem(this.sessionKey, JSON.stringify(sessions))
            
            this.logger.info("Session stored", { topic: session.topic })
            
        } CATCH error {
            this.logger.error("Failed to store session", error)
        }
    }
    
    // TEST: Should retrieve stored sessions correctly
    // TEST: Should handle corrupted storage data
    FUNCTION getStoredSessions(): Object {
        TRY {
            sessionsData = this.storage.getItem(this.sessionKey)
            IF NOT sessionsData {
                RETURN {}
            }
            
            RETURN JSON.parse(sessionsData)
            
        } CATCH error {
            this.logger.error("Failed to retrieve sessions", error)
            RETURN {}
        }
    }
    
    // TEST: Should remove session correctly
    // TEST: Should handle non-existent sessions
    FUNCTION removeSession(topic: String): Void {
        TRY {
            sessions = this.getStoredSessions()
            DELETE sessions[topic]
            
            this.storage.setItem(this.sessionKey, JSON.stringify(sessions))
            
            this.logger.info("Session removed", { topic })
            
        } CATCH error {
            this.logger.error("Failed to remove session", error)
        }
    }
    
    // TEST: Should clear all sessions
    FUNCTION clearSessions(): Void {
        TRY {
            this.storage.removeItem(this.sessionKey)
            this.logger.info("All sessions cleared")
            
        } CATCH error {
            this.logger.error("Failed to clear sessions", error)
        }
    }
    
    // TEST: Should sanitize session data correctly
    // TEST: Should remove sensitive information
    PRIVATE FUNCTION sanitizeSession(session: Session): Object {
        // Remove or encrypt sensitive data before storage
        RETURN {
            topic: session.topic,
            expiry: session.expiry,
            acknowledged: session.acknowledged,
            namespaces: session.namespaces,
            peer: {
                metadata: session.peer.metadata
            }
            // Exclude sensitive relay and controller data
        }
    }
}
```

## Module: Configuration and Types

```pseudocode
// Configuration interfaces
INTERFACE WalletConnectConfig {
    projectId: String
    metadata: {
        name: String
        description: String
        url: String
        icons: Array<String>
    }
    relayUrl?: String
    supportedChains?: Array<ChainId>
    sessionProperties?: Object
}

INTERFACE SessionAccount {
    namespace: String
    chainId: ChainId
    address: String
}

// Error types
ENUM WalletConnectError {
    PROVIDER_UNAVAILABLE,
    CONNECTION_TIMEOUT,
    USER_REJECTED_REQUEST,
    NO_ACTIVE_SESSION,
    NO_ACTIVE_ACCOUNT,
    UNSUPPORTED_CHAIN,
    INVALID_MESSAGE,
    SESSION_EXPIRED,
    INVALID_SESSION_DATA,
    QR_CODE_GENERATION_FAILED
}

// QR Code generator
CLASS QRCodeGenerator {
    // TEST: Should generate QR code from URI
    // TEST: Should handle invalid URIs
    FUNCTION generate(uri: String): Promise<String> {
        IF NOT uri OR uri.length === 0 {
            THROW NEW Error(INVALID_URI)
        }
        
        TRY {
            // Generate QR code as data URL or SVG
            qrCode = AWAIT this.generateQRCode(uri)
            RETURN qrCode
            
        } CATCH error {
            THROW NEW Error(QR_CODE_GENERATION_FAILED, error.message)
        }
    }
}
```

## Integration Points

### 1. Universal Wallet Interface
- Implements WalletProvider interface for seamless integration
- Supports all standard wallet operations
- Provides consistent event handling

### 2. Session Management
- Persistent session storage and recovery
- Automatic session validation and cleanup
- Multi-session support for different dApps

### 3. Multi-Chain Support
- Dynamic namespace management
- Chain switching and addition
- Cross-chain account management

### 4. QR Code Integration
- Real-time QR code generation
- URI validation and formatting
- Mobile wallet deep linking

## Security Considerations

### 1. Session Security
- Secure session data storage
- Session expiry validation
- Encrypted sensitive data

### 2. Request Validation
- Validate all incoming requests
- Verify session authenticity
- Prevent replay attacks

### 3. URI Security
- Validate WalletConnect URIs
- Prevent malicious URI injection
- Secure QR code generation

### 4. Network Security
- Secure relay communication
- End-to-end encryption
- Message integrity verification

## Performance Considerations

### 1. Connection Optimization
- Efficient session restoration
- Optimized QR code generation
- Minimal connection latency

### 2. Memory Management
- Efficient session storage
- Cleanup of expired sessions
- Optimized event handling

### 3. Network Efficiency
- Batched requests when possible
- Connection pooling
- Retry mechanisms with backoff

---

*This pseudocode specification completes the WalletConnect v2 integration with comprehensive TDD anchors covering QR code sessions, mobile wallet communication, and multi-chain support.*