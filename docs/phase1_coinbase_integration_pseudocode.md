# Phase 1: Coinbase Integration - Pseudocode Specification

## Overview

This document provides the pseudocode specification for Coinbase integration, including both fiat onramp capabilities and Coinbase Wallet integration for Phase 1 of the Grekko DeFi trading platform.

## Module: CoinbaseClient

```pseudocode
// Main Coinbase integration client
CLASS CoinbaseClient IMPLEMENTS WalletProvider {
    PRIVATE apiClient: CoinbaseAPIClient
    PRIVATE walletSDK: CoinbaseWalletSDK
    PRIVATE config: CoinbaseConfig
    PRIVATE eventEmitter: EventEmitter
    PRIVATE logger: Logger
    PRIVATE rateLimiter: RateLimiter
    
    // Provider identity
    READONLY providerId = "coinbase"
    READONLY name = "Coinbase"
    READONLY version: String
    READONLY supportedChains: Array<ChainId>
    READONLY capabilities: Array<WalletCapability>
    
    // Connection state
    isAvailable: Boolean = false
    isConnected: Boolean = false
    connectionState: ConnectionState = DISCONNECTED
    
    // TEST: Should initialize with valid configuration
    // TEST: Should validate API credentials on initialization
    // TEST: Should setup rate limiting correctly
    CONSTRUCTOR(config: CoinbaseConfig) {
        this.config = this.validateConfig(config)
        this.apiClient = NEW CoinbaseAPIClient(config.apiCredentials)
        this.walletSDK = NEW CoinbaseWalletSDK(config.walletConfig)
        this.eventEmitter = NEW EventEmitter()
        this.logger = NEW Logger("CoinbaseClient")
        this.rateLimiter = NEW RateLimiter(maxRequests: 100, windowMs: 60000)
        
        this.version = config.version || "1.0.0"
        this.supportedChains = config.supportedChains || [ETHEREUM, POLYGON, BASE]
        this.capabilities = [
            SIGN_MESSAGE, SIGN_TRANSACTION, SEND_TRANSACTION,
            SWITCH_CHAIN, FIAT_ONRAMP
        ]
        
        this.initializeProvider()
    }
    
    // TEST: Should successfully connect when provider is available
    // TEST: Should reject connection when provider unavailable
    // TEST: Should handle connection timeout
    // TEST: Should enforce rate limiting
    FUNCTION connect(options: ConnectionOptions = {}): Promise<WalletConnection> {
        // Rate limiting check
        IF NOT this.rateLimiter.checkLimit("connect") {
            THROW NEW Error(RATE_LIMIT_EXCEEDED)
        }
        
        // Validate provider availability
        IF NOT this.isAvailable {
            THROW NEW Error(PROVIDER_UNAVAILABLE)
        }
        
        // Check if already connected
        IF this.isConnected {
            RETURN this.getCurrentConnection()
        }
        
        this.connectionState = CONNECTING
        
        TRY {
            // Initialize wallet SDK connection
            walletConnection = AWAIT this.walletSDK.connect({
                chainId: options.chainId || ETHEREUM,
                timeout: options.timeout || 30000
            })
            
            // Verify API connectivity
            AWAIT this.verifyAPIConnectivity()
            
            // Create connection object
            connection = this.createWalletConnection(walletConnection, options)
            
            // Setup event listeners
            this.setupConnectionEventListeners(connection)
            
            // Update state
            this.isConnected = true
            this.connectionState = CONNECTED
            
            // Emit connection event
            this.eventEmitter.emit("connect", {
                connectionId: connection.connectionId,
                accounts: connection.accounts,
                chainId: connection.chainId
            })
            
            this.logger.info("Coinbase wallet connected", {
                connectionId: connection.connectionId,
                accountCount: connection.accounts.length
            })
            
            RETURN connection
            
        } CATCH error {
            this.connectionState = ERROR
            this.logger.error("Coinbase connection failed", error)
            THROW NEW Error(CONNECTION_FAILED, error.message)
        }
    }
    
    // TEST: Should successfully disconnect active connection
    // TEST: Should handle disconnection when not connected
    // TEST: Should clean up event listeners
    FUNCTION disconnect(): Promise<Void> {
        IF NOT this.isConnected {
            RETURN
        }
        
        this.connectionState = DISCONNECTING
        
        TRY {
            // Disconnect wallet SDK
            AWAIT this.walletSDK.disconnect()
            
            // Clean up event listeners
            this.removeConnectionEventListeners()
            
            // Update state
            this.isConnected = false
            this.connectionState = DISCONNECTED
            
            // Emit disconnection event
            this.eventEmitter.emit("disconnect", {
                providerId: this.providerId
            })
            
            this.logger.info("Coinbase wallet disconnected")
            
        } CATCH error {
            this.logger.error("Coinbase disconnection failed", error)
            THROW NEW Error(DISCONNECTION_FAILED, error.message)
        }
    }
    
    // TEST: Should return connected accounts
    // TEST: Should handle API errors gracefully
    // TEST: Should cache account data appropriately
    FUNCTION getAccounts(): Promise<Array<Account>> {
        IF NOT this.isConnected {
            THROW NEW Error(NOT_CONNECTED)
        }
        
        TRY {
            // Get accounts from wallet SDK
            walletAccounts = AWAIT this.walletSDK.getAccounts()
            
            // Get additional account info from API
            accounts = []
            FOR walletAccount IN walletAccounts {
                accountInfo = AWAIT this.apiClient.getAccountInfo(walletAccount.address)
                
                account = {
                    address: walletAccount.address,
                    name: accountInfo.name || `Account ${accounts.length + 1}`,
                    balance: AWAIT this.getAccountBalances(walletAccount.address),
                    isActive: walletAccount.isActive
                }
                
                accounts.push(account)
            }
            
            RETURN accounts
            
        } CATCH error {
            this.logger.error("Failed to get accounts", error)
            THROW NEW Error(ACCOUNT_FETCH_FAILED, error.message)
        }
    }
    
    // TEST: Should successfully switch to supported chain
    // TEST: Should reject unsupported chain
    // TEST: Should handle user rejection
    FUNCTION switchChain(chainId: ChainId): Promise<Void> {
        IF NOT this.supportedChains.includes(chainId) {
            THROW NEW Error(UNSUPPORTED_CHAIN)
        }
        
        TRY {
            AWAIT this.walletSDK.switchChain(chainId)
            
            this.eventEmitter.emit("chainChanged", {
                chainId,
                providerId: this.providerId
            })
            
            this.logger.info("Chain switched", { chainId })
            
        } CATCH error {
            this.logger.error("Chain switch failed", error)
            THROW NEW Error(CHAIN_SWITCH_FAILED, error.message)
        }
    }
    
    // TEST: Should successfully sign message
    // TEST: Should validate message format
    // TEST: Should handle user rejection
    FUNCTION signMessage(message: String): Promise<String> {
        IF NOT this.isConnected {
            THROW NEW Error(NOT_CONNECTED)
        }
        
        // Validate message
        IF message IS EMPTY OR message.length > 1000 {
            THROW NEW Error(INVALID_MESSAGE)
        }
        
        TRY {
            signature = AWAIT this.walletSDK.signMessage(message)
            
            this.logger.info("Message signed", {
                messageLength: message.length,
                signatureLength: signature.length
            })
            
            RETURN signature
            
        } CATCH error {
            this.logger.error("Message signing failed", error)
            THROW NEW Error(SIGNING_FAILED, error.message)
        }
    }
    
    // TEST: Should successfully sign transaction
    // TEST: Should validate transaction parameters
    // TEST: Should estimate gas correctly
    FUNCTION signTransaction(transaction: TransactionRequest): Promise<SignedTransaction> {
        IF NOT this.isConnected {
            THROW NEW Error(NOT_CONNECTED)
        }
        
        // Validate transaction
        validatedTx = this.validateTransaction(transaction)
        
        TRY {
            // Estimate gas if not provided
            IF NOT validatedTx.gasLimit {
                validatedTx.gasLimit = AWAIT this.estimateGas(validatedTx)
            }
            
            // Sign transaction
            signedTx = AWAIT this.walletSDK.signTransaction(validatedTx)
            
            this.logger.info("Transaction signed", {
                to: validatedTx.to,
                value: validatedTx.value.toString(),
                gasLimit: validatedTx.gasLimit.toString()
            })
            
            RETURN signedTx
            
        } CATCH error {
            this.logger.error("Transaction signing failed", error)
            THROW NEW Error(SIGNING_FAILED, error.message)
        }
    }
    
    // TEST: Should successfully send transaction
    // TEST: Should monitor transaction status
    // TEST: Should handle network errors
    FUNCTION sendTransaction(transaction: TransactionRequest): Promise<TransactionHash> {
        signedTx = AWAIT this.signTransaction(transaction)
        
        TRY {
            txHash = AWAIT this.walletSDK.sendTransaction(signedTx)
            
            // Start monitoring transaction
            this.monitorTransaction(txHash)
            
            this.logger.info("Transaction sent", { txHash })
            
            RETURN txHash
            
        } CATCH error {
            this.logger.error("Transaction send failed", error)
            THROW NEW Error(SEND_FAILED, error.message)
        }
    }
    
    // TEST: Should validate configuration parameters
    // TEST: Should reject invalid API credentials
    // TEST: Should validate supported chains
    PRIVATE FUNCTION validateConfig(config: CoinbaseConfig): CoinbaseConfig {
        IF NOT config.apiCredentials OR NOT config.apiCredentials.apiKey {
            THROW NEW Error(INVALID_API_CREDENTIALS)
        }
        
        IF NOT config.walletConfig OR NOT config.walletConfig.appName {
            THROW NEW Error(INVALID_WALLET_CONFIG)
        }
        
        IF config.supportedChains AND config.supportedChains.length === 0 {
            THROW NEW Error(INVALID_SUPPORTED_CHAINS)
        }
        
        RETURN config
    }
    
    // TEST: Should initialize provider availability
    // TEST: Should setup SDK configurations
    PRIVATE FUNCTION initializeProvider(): Promise<Void> {
        TRY {
            // Check API connectivity
            AWAIT this.apiClient.ping()
            
            // Initialize wallet SDK
            AWAIT this.walletSDK.initialize()
            
            this.isAvailable = true
            this.logger.info("Coinbase provider initialized")
            
        } CATCH error {
            this.isAvailable = false
            this.logger.error("Coinbase provider initialization failed", error)
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

## Module: CoinbaseFiatOnramp

```pseudocode
// Coinbase fiat onramp integration
CLASS CoinbaseFiatOnramp {
    PRIVATE apiClient: CoinbaseAPIClient
    PRIVATE config: OnrampConfig
    PRIVATE logger: Logger
    PRIVATE eventBus: EventBus
    PRIVATE kycService: KYCService
    PRIVATE complianceService: ComplianceService
    
    // TEST: Should initialize with valid configuration
    CONSTRUCTOR(config: OnrampConfig, eventBus: EventBus) {
        this.config = this.validateOnrampConfig(config)
        this.apiClient = NEW CoinbaseAPIClient(config.apiCredentials)
        this.logger = NEW Logger("CoinbaseFiatOnramp")
        this.eventBus = eventBus
        this.kycService = NEW KYCService(config.kycConfig)
        this.complianceService = NEW ComplianceService(config.complianceConfig)
    }
    
    // TEST: Should successfully initiate fiat onramp
    // TEST: Should validate fiat amount and currency
    // TEST: Should check user eligibility
    // TEST: Should handle KYC requirements
    FUNCTION initiateFiatOnramp(request: FiatOnrampRequest): Promise<FiatOnramp> {
        // Validate request
        validatedRequest = this.validateOnrampRequest(request)
        
        // Check user eligibility
        eligibilityCheck = AWAIT this.checkUserEligibility(validatedRequest.userId)
        IF NOT eligibilityCheck.isEligible {
            THROW NEW Error(USER_NOT_ELIGIBLE, eligibilityCheck.reason)
        }
        
        // Check KYC status
        kycStatus = AWAIT this.kycService.getKYCStatus(validatedRequest.userId)
        IF kycStatus !== KYCStatus.APPROVED {
            // Initiate KYC process if needed
            IF kycStatus === KYCStatus.NOT_STARTED {
                AWAIT this.kycService.initiateKYC(validatedRequest.userId)
            }
            THROW NEW Error(KYC_REQUIRED, kycStatus)
        }
        
        // Run compliance checks
        complianceResult = AWAIT this.complianceService.runChecks(validatedRequest)
        IF NOT complianceResult.passed {
            THROW NEW Error(COMPLIANCE_FAILED, complianceResult.reason)
        }
        
        TRY {
            // Create onramp transaction
            onrampId = this.generateOnrampId()
            
            // Get exchange rate
            exchangeRate = AWAIT this.getExchangeRate(
                validatedRequest.fiatCurrency,
                validatedRequest.cryptoAsset
            )
            
            // Calculate crypto amount
            cryptoAmount = this.calculateCryptoAmount(
                validatedRequest.fiatAmount,
                exchangeRate
            )
            
            // Calculate fees
            fees = AWAIT this.calculateFees(validatedRequest)
            
            // Create onramp record
            onramp = {
                onrampId,
                providerId: "coinbase",
                externalId: NULL, // Will be set when payment is initiated
                fiatAmount: validatedRequest.fiatAmount,
                fiatCurrency: validatedRequest.fiatCurrency,
                cryptoAmount,
                cryptoAsset: validatedRequest.cryptoAsset,
                userId: validatedRequest.userId,
                destinationAddress: validatedRequest.destinationAddress,
                kycStatus: KYCStatus.APPROVED,
                complianceChecks: complianceResult.checks,
                status: OnrampStatus.INITIATED,
                statusHistory: [{
                    status: OnrampStatus.INITIATED,
                    timestamp: NEW Date(),
                    message: "Onramp transaction initiated"
                }],
                initiatedAt: NEW Date(),
                expiresAt: NEW Date(Date.now() + 24 * 60 * 60 * 1000), // 24 hours
                fees,
                exchangeRate
            }
            
            // Store onramp record
            AWAIT this.storeOnrampRecord(onramp)
            
            // Initiate payment with Coinbase
            paymentResult = AWAIT this.initiatePayment(onramp)
            onramp.externalId = paymentResult.paymentId
            onramp.status = OnrampStatus.PAYMENT_PENDING
            
            // Update record
            AWAIT this.updateOnrampRecord(onramp)
            
            // Emit event
            this.eventBus.emit("onramp.initiated", {
                onrampId,
                userId: validatedRequest.userId,
                fiatAmount: validatedRequest.fiatAmount,
                cryptoAmount
            })
            
            this.logger.info("Fiat onramp initiated", {
                onrampId,
                fiatAmount: validatedRequest.fiatAmount,
                cryptoAmount
            })
            
            RETURN onramp
            
        } CATCH error {
            this.logger.error("Fiat onramp initiation failed", error)
            THROW NEW Error(ONRAMP_INITIATION_FAILED, error.message)
        }
    }
    
    // TEST: Should return current onramp status
    // TEST: Should handle non-existent onramp ID
    FUNCTION getOnrampStatus(onrampId: String): Promise<OnrampStatus> {
        onramp = AWAIT this.getOnrampRecord(onrampId)
        IF onramp IS NULL {
            THROW NEW Error(ONRAMP_NOT_FOUND)
        }
        
        // Check for status updates from Coinbase
        AWAIT this.syncOnrampStatus(onramp)
        
        RETURN onramp.status
    }
    
    // TEST: Should handle webhook notifications correctly
    // TEST: Should validate webhook signatures
    // TEST: Should update onramp status appropriately
    FUNCTION handleWebhook(webhookData: WebhookData): Promise<Void> {
        // Validate webhook signature
        IF NOT this.validateWebhookSignature(webhookData) {
            THROW NEW Error(INVALID_WEBHOOK_SIGNATURE)
        }
        
        // Parse webhook payload
        payload = this.parseWebhookPayload(webhookData.payload)
        
        // Find corresponding onramp
        onramp = AWAIT this.getOnrampByExternalId(payload.paymentId)
        IF onramp IS NULL {
            this.logger.warn("Webhook for unknown onramp", { paymentId: payload.paymentId })
            RETURN
        }
        
        // Update onramp status based on webhook
        SWITCH payload.eventType {
            CASE "payment.completed":
                AWAIT this.handlePaymentCompleted(onramp, payload)
                BREAK
            CASE "payment.failed":
                AWAIT this.handlePaymentFailed(onramp, payload)
                BREAK
            CASE "crypto.delivered":
                AWAIT this.handleCryptoDelivered(onramp, payload)
                BREAK
            DEFAULT:
                this.logger.info("Unhandled webhook event", { eventType: payload.eventType })
        }
    }
    
    // TEST: Should validate all required request fields
    // TEST: Should validate fiat amount limits
    // TEST: Should validate destination address format
    PRIVATE FUNCTION validateOnrampRequest(request: FiatOnrampRequest): FiatOnrampRequest {
        IF NOT request.userId OR request.userId.length === 0 {
            THROW NEW Error(INVALID_USER_ID)
        }
        
        IF NOT request.fiatAmount OR request.fiatAmount <= 0 {
            THROW NEW Error(INVALID_FIAT_AMOUNT)
        }
        
        IF request.fiatAmount < this.config.minFiatAmount {
            THROW NEW Error(AMOUNT_TOO_SMALL)
        }
        
        IF request.fiatAmount > this.config.maxFiatAmount {
            THROW NEW Error(AMOUNT_TOO_LARGE)
        }
        
        IF NOT this.config.supportedFiatCurrencies.includes(request.fiatCurrency) {
            THROW NEW Error(UNSUPPORTED_FIAT_CURRENCY)
        }
        
        IF NOT this.config.supportedCryptoAssets.includes(request.cryptoAsset) {
            THROW NEW Error(UNSUPPORTED_CRYPTO_ASSET)
        }
        
        IF NOT this.isValidAddress(request.destinationAddress, request.cryptoAsset) {
            THROW NEW Error(INVALID_DESTINATION_ADDRESS)
        }
        
        RETURN request
    }
    
    // TEST: Should check geographic restrictions
    // TEST: Should check account limits
    // TEST: Should check blacklist status
    PRIVATE FUNCTION checkUserEligibility(userId: String): Promise<EligibilityResult> {
        TRY {
            // Get user profile
            userProfile = AWAIT this.apiClient.getUserProfile(userId)
            
            // Check geographic restrictions
            IF NOT this.config.allowedCountries.includes(userProfile.country) {
                RETURN {
                    isEligible: false,
                    reason: "Geographic restriction"
                }
            }
            
            // Check account limits
            accountLimits = AWAIT this.apiClient.getAccountLimits(userId)
            IF accountLimits.dailyRemaining <= 0 {
                RETURN {
                    isEligible: false,
                    reason: "Daily limit exceeded"
                }
            }
            
            // Check blacklist
            isBlacklisted = AWAIT this.complianceService.checkBlacklist(userId)
            IF isBlacklisted {
                RETURN {
                    isEligible: false,
                    reason: "Account restricted"
                }
            }
            
            RETURN {
                isEligible: true,
                reason: NULL
            }
            
        } CATCH error {
            this.logger.error("Eligibility check failed", error)
            RETURN {
                isEligible: false,
                reason: "Eligibility check failed"
            }
        }
    }
    
    // TEST: Should get current exchange rates
    // TEST: Should handle rate fetch errors
    // TEST: Should cache rates appropriately
    PRIVATE FUNCTION getExchangeRate(fiatCurrency: String, cryptoAsset: String): Promise<BigNumber> {
        TRY {
            rate = AWAIT this.apiClient.getExchangeRate(fiatCurrency, cryptoAsset)
            RETURN rate
        } CATCH error {
            this.logger.error("Failed to get exchange rate", error)
            THROW NEW Error(EXCHANGE_RATE_UNAVAILABLE)
        }
    }
    
    // TEST: Should calculate fees correctly
    // TEST: Should apply fee tiers based on amount
    PRIVATE FUNCTION calculateFees(request: FiatOnrampRequest): Promise<Array<Fee>> {
        fees = []
        
        // Base processing fee
        processingFee = request.fiatAmount * this.config.processingFeeRate
        fees.push({
            type: "processing",
            amount: processingFee,
            currency: request.fiatCurrency
        })
        
        // Network fee (if applicable)
        IF this.config.networkFeeEnabled {
            networkFee = AWAIT this.estimateNetworkFee(request.cryptoAsset)
            fees.push({
                type: "network",
                amount: networkFee,
                currency: request.cryptoAsset
            })
        }
        
        RETURN fees
    }
}
```

## Module: Configuration and Types

```pseudocode
// Configuration interfaces
INTERFACE CoinbaseConfig {
    apiCredentials: {
        apiKey: String
        apiSecret: String
        passphrase: String
        sandbox: Boolean
    }
    walletConfig: {
        appName: String
        appLogoUrl: String
        darkMode: Boolean
    }
    supportedChains: Array<ChainId>
    version: String
}

INTERFACE OnrampConfig {
    apiCredentials: APICredentials
    kycConfig: KYCConfig
    complianceConfig: ComplianceConfig
    minFiatAmount: Number
    maxFiatAmount: Number
    supportedFiatCurrencies: Array<String>
    supportedCryptoAssets: Array<String>
    allowedCountries: Array<String>
    processingFeeRate: Number
    networkFeeEnabled: Boolean
}

// Request and response types
INTERFACE FiatOnrampRequest {
    userId: String
    fiatAmount: BigNumber
    fiatCurrency: String
    cryptoAsset: String
    destinationAddress: String
    paymentMethod?: String
}

INTERFACE EligibilityResult {
    isEligible: Boolean
    reason: String?
}

// Error types
ENUM OnrampError {
    INVALID_USER_ID,
    INVALID_FIAT_AMOUNT,
    AMOUNT_TOO_SMALL,
    AMOUNT_TOO_LARGE,
    UNSUPPORTED_FIAT_CURRENCY,
    UNSUPPORTED_CRYPTO_ASSET,
    INVALID_DESTINATION_ADDRESS,
    USER_NOT_ELIGIBLE,
    KYC_REQUIRED,
    COMPLIANCE_FAILED,
    ONRAMP_INITIATION_FAILED,
    EXCHANGE_RATE_UNAVAILABLE
}
```

## Integration Points

### 1. WalletProvider Integration
- Implements the universal WalletProvider interface
- Provides seamless integration with WalletConnectionManager
- Supports all required wallet capabilities

### 2. Event System Integration
- Emits standardized wallet events
- Integrates with central event bus
- Supports real-time status updates

### 3. KYC/Compliance Integration
- Integrates with external KYC providers
- Supports automated compliance checking
- Handles regulatory requirements

### 4. API Rate Limiting
- Implements rate limiting for API calls
- Prevents API quota exhaustion
- Supports burst and sustained rate limits

## Security Considerations

### 1. API Security
- Secure credential storage and rotation
- Request signing and authentication
- HTTPS-only communication

### 2. Webhook Security
- Signature validation for all webhooks
- Replay attack prevention
- Secure payload parsing

### 3. Data Protection
- Encryption of sensitive user data
- Secure handling of financial information
- Compliance with data protection regulations

---

*This pseudocode specification provides comprehensive coverage of Coinbase integration with TDD anchors for both wallet and fiat onramp functionality.*