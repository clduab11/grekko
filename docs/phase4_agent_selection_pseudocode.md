# Phase 4: Agent Selection Interface - AI Trading Agents Pseudocode

## Module Overview

This module defines the AI agent selection interface with three distinct trading agents: Spot (tutor), Gordo (semi-autonomous), and Gordon Gekko (autonomous). Includes permission management, configuration, and real-time performance monitoring.

## Core Components

### AgentSidebarController

```typescript
class AgentSidebarController {
    private agentRegistry: AgentRegistry
    private configurationManager: AgentConfigurationManager
    private performanceMonitor: AgentPerformanceMonitor
    private permissionManager: PermissionManager
    
    // TEST: Agent sidebar initializes with all three agents
    initialize(): void {
        this.agentRegistry = new AgentRegistry()
        this.configurationManager = new AgentConfigurationManager()
        this.performanceMonitor = new AgentPerformanceMonitor()
        this.permissionManager = new PermissionManager()
        
        // Register the three core agents
        this.registerCoreAgents()
        
        // Setup UI components
        this.setupAgentSelectionUI()
        
        // Initialize performance monitoring
        this.startPerformanceMonitoring()
        
        // Setup event listeners
        this.setupEventListeners()
    }
    
    // TEST: Core agents register with correct configurations
    private registerCoreAgents(): void {
        // Register Spot - The Tutor Agent
        const spotAgent = new SpotTutorAgent({
            agentId: 'spot-tutor',
            name: 'Spot',
            description: 'Educational trading assistant that identifies trends and provides learning insights',
            autonomyLevel: AutonomyLevel.TUTOR,
            capabilities: [
                AgentCapability.TREND_ANALYSIS,
                AgentCapability.EDUCATIONAL_INSIGHTS,
                AgentCapability.MARKET_EXPLANATION,
                AgentCapability.RISK_EDUCATION
            ],
            riskParameters: {
                maxPositionSize: 0, // No trading capability
                maxDailyLoss: 0,
                stopLossPercentage: 0,
                takeProfitPercentage: 0,
                maxOpenPositions: 0
            }
        })
        
        // Register Gordo - The Semi-Autonomous Agent
        const gordoAgent = new GordoSemiAutonomousAgent({
            agentId: 'gordo-semi',
            name: 'Gordo',
            description: 'Permission-based trading assistant that executes trades with user approval',
            autonomyLevel: AutonomyLevel.SEMI_AUTONOMOUS,
            capabilities: [
                AgentCapability.TREND_ANALYSIS,
                AgentCapability.TRADE_EXECUTION,
                AgentCapability.RISK_MANAGEMENT,
                AgentCapability.PORTFOLIO_OPTIMIZATION,
                AgentCapability.PERMISSION_REQUESTS
            ],
            riskParameters: {
                maxPositionSize: 1000, // $1000 default
                maxDailyLoss: 100,     // $100 default
                stopLossPercentage: 5,  // 5% default
                takeProfitPercentage: 10, // 10% default
                maxOpenPositions: 3
            }
        })
        
        // Register Gordon Gekko - The Autonomous Agent
        const gekkoAgent = new GordonGekkoAutonomousAgent({
            agentId: 'gekko-auto',
            name: 'Gordon Gekko',
            description: 'Fully autonomous trading agent with advanced strategies and risk management',
            autonomyLevel: AutonomyLevel.AUTONOMOUS,
            capabilities: [
                AgentCapability.TREND_ANALYSIS,
                AgentCapability.TRADE_EXECUTION,
                AgentCapability.RISK_MANAGEMENT,
                AgentCapability.PORTFOLIO_OPTIMIZATION,
                AgentCapability.ADVANCED_STRATEGIES,
                AgentCapability.MARKET_MAKING,
                AgentCapability.ARBITRAGE_DETECTION
            ],
            riskParameters: {
                maxPositionSize: 5000,  // $5000 default
                maxDailyLoss: 500,      // $500 default
                stopLossPercentage: 3,   // 3% default
                takeProfitPercentage: 15, // 15% default
                maxOpenPositions: 10
            }
        })
        
        this.agentRegistry.register(spotAgent)
        this.agentRegistry.register(gordoAgent)
        this.agentRegistry.register(gekkoAgent)
    }
    
    // TEST: Agent selection UI renders correctly
    private setupAgentSelectionUI(): void {
        const sidebarContainer = document.getElementById('right-sidebar')
        
        const agentSelectionHTML = `
            <div class="agent-sidebar">
                <div class="agent-header">
                    <h2>AI Trading Agents</h2>
                    <div class="agent-status-indicator" id="agent-status"></div>
                </div>
                
                <div class="agent-list" id="agent-list">
                    <!-- Agent cards will be populated here -->
                </div>
                
                <div class="agent-configuration" id="agent-config">
                    <!-- Configuration panel will be shown here -->
                </div>
                
                <div class="agent-performance" id="agent-performance">
                    <!-- Performance metrics will be displayed here -->
                </div>
            </div>
        `
        
        sidebarContainer.innerHTML = agentSelectionHTML
        
        // Populate agent cards
        this.populateAgentCards()
    }
    
    // TEST: Agent cards display correct information
    private populateAgentCards(): void {
        const agentListContainer = document.getElementById('agent-list')
        const agents = this.agentRegistry.getAllAgents()
        
        agents.forEach(agent => {
            const agentCard = this.createAgentCard(agent)
            agentListContainer.appendChild(agentCard)
        })
    }
    
    // TEST: Agent card creation includes all required elements
    private createAgentCard(agent: TradingAgent): HTMLElement {
        const card = document.createElement('div')
        card.className = 'agent-card'
        card.setAttribute('data-agent-id', agent.agentId)
        
        const statusClass = this.getAgentStatusClass(agent.status)
        const autonomyBadge = this.getAutonomyBadge(agent.autonomyLevel)
        
        card.innerHTML = `
            <div class="agent-card-header">
                <div class="agent-avatar">
                    <img src="assets/agents/${agent.agentId}.png" alt="${agent.name}" />
                </div>
                <div class="agent-info">
                    <h3>${agent.name}</h3>
                    <span class="autonomy-badge ${autonomyBadge.class}">${autonomyBadge.text}</span>
                </div>
                <div class="agent-status ${statusClass}">
                    <span class="status-indicator"></span>
                </div>
            </div>
            
            <div class="agent-description">
                <p>${agent.description}</p>
            </div>
            
            <div class="agent-capabilities">
                ${agent.capabilities.map(cap => `<span class="capability-tag">${cap}</span>`).join('')}
            </div>
            
            <div class="agent-actions">
                <button class="btn-select" onclick="selectAgent('${agent.agentId}')">
                    ${agent.status === AgentStatus.ACTIVE ? 'Configure' : 'Activate'}
                </button>
                <button class="btn-performance" onclick="showPerformance('${agent.agentId}')">
                    Performance
                </button>
            </div>
        `
        
        return card
    }
    
    // TEST: Agent selection triggers correct workflow
    selectAgent(agentId: string): void {
        const agent = this.agentRegistry.getAgent(agentId)
        
        if (!agent) {
            throw new Error(`Agent not found: ${agentId}`)
        }
        
        // Deactivate current agent if any
        this.deactivateCurrentAgent()
        
        // Check permissions for agent activation
        if (agent.autonomyLevel !== AutonomyLevel.TUTOR) {
            this.requestAgentPermissions(agent)
        } else {
            this.activateAgent(agent)
        }
        
        // Show configuration panel
        this.showConfigurationPanel(agent)
        
        // Update UI state
        this.updateAgentSelectionUI(agent)
    }
    
    // TEST: Permission requests work correctly for autonomous agents
    private requestAgentPermissions(agent: TradingAgent): void {
        const permissionModal = this.createPermissionModal(agent)
        document.body.appendChild(permissionModal)
        
        // Show modal with permission details
        permissionModal.classList.add('show')
        
        // Setup permission handlers
        this.setupPermissionHandlers(agent, permissionModal)
    }
    
    // TEST: Permission modal displays correct information
    private createPermissionModal(agent: TradingAgent): HTMLElement {
        const modal = document.createElement('div')
        modal.className = 'permission-modal'
        modal.id = `permission-modal-${agent.agentId}`
        
        const riskLevel = this.calculateRiskLevel(agent.riskParameters)
        const permissionList = this.generatePermissionList(agent)
        
        modal.innerHTML = `
            <div class="modal-overlay">
                <div class="modal-content">
                    <div class="modal-header">
                        <h2>Agent Activation Permissions</h2>
                        <span class="risk-level ${riskLevel.class}">${riskLevel.text}</span>
                    </div>
                    
                    <div class="modal-body">
                        <div class="agent-summary">
                            <h3>${agent.name}</h3>
                            <p>${agent.description}</p>
                        </div>
                        
                        <div class="permission-details">
                            <h4>This agent will be able to:</h4>
                            <ul class="permission-list">
                                ${permissionList.map(permission => `
                                    <li class="permission-item ${permission.risk}">
                                        <span class="permission-icon">${permission.icon}</span>
                                        <span class="permission-text">${permission.text}</span>
                                        <span class="permission-limit">${permission.limit}</span>
                                    </li>
                                `).join('')}
                            </ul>
                        </div>
                        
                        <div class="risk-parameters">
                            <h4>Risk Limits:</h4>
                            <div class="risk-grid">
                                <div class="risk-item">
                                    <label>Max Position Size:</label>
                                    <span>$${agent.riskParameters.maxPositionSize}</span>
                                </div>
                                <div class="risk-item">
                                    <label>Max Daily Loss:</label>
                                    <span>$${agent.riskParameters.maxDailyLoss}</span>
                                </div>
                                <div class="risk-item">
                                    <label>Stop Loss:</label>
                                    <span>${agent.riskParameters.stopLossPercentage}%</span>
                                </div>
                                <div class="risk-item">
                                    <label>Max Positions:</label>
                                    <span>${agent.riskParameters.maxOpenPositions}</span>
                                </div>
                            </div>
                        </div>
                    </div>
                    
                    <div class="modal-footer">
                        <button class="btn-cancel" onclick="cancelPermission('${agent.agentId}')">
                            Cancel
                        </button>
                        <button class="btn-approve" onclick="approvePermission('${agent.agentId}')">
                            Approve & Activate
                        </button>
                    </div>
                </div>
            </div>
        `
        
        return modal
    }
    
    // TEST: Permission approval activates agent correctly
    approvePermission(agentId: string): void {
        const agent = this.agentRegistry.getAgent(agentId)
        
        // Record permission grant
        this.permissionManager.grantPermissions(agentId, {
            tradingEnabled: true,
            riskParameters: agent.riskParameters,
            grantedAt: new Date(),
            grantedBy: 'user' // In production, use actual user ID
        })
        
        // Activate the agent
        this.activateAgent(agent)
        
        // Close permission modal
        this.closePermissionModal(agentId)
        
        // Show success notification
        this.showNotification({
            type: 'success',
            message: `${agent.name} has been activated with trading permissions`
        })
    }
    
    // TEST: Agent activation updates status correctly
    private activateAgent(agent: TradingAgent): void {
        // Update agent status
        agent.status = AgentStatus.ACTIVE
        
        // Start agent processes
        agent.start()
        
        // Begin performance monitoring
        this.performanceMonitor.startMonitoring(agent.agentId)
        
        // Update registry
        this.agentRegistry.updateAgent(agent)
        
        // Emit activation event
        this.emitAgentEvent('agentActivated', {
            agentId: agent.agentId,
            timestamp: new Date()
        })
    }
    
    // TEST: Configuration panel displays correctly
    private showConfigurationPanel(agent: TradingAgent): void {
        const configContainer = document.getElementById('agent-config')
        
        const configPanel = this.createConfigurationPanel(agent)
        configContainer.innerHTML = ''
        configContainer.appendChild(configPanel)
    }
    
    // TEST: Configuration saving works correctly
    saveConfiguration(agentId: string): void {
        const agent = this.agentRegistry.getAgent(agentId)
        
        // Collect configuration from form
        const newConfig = this.collectConfigurationFromForm(agentId)
        
        // Validate configuration
        this.validateConfiguration(newConfig, agent.autonomyLevel)
        
        // Update agent configuration
        agent.configuration = { ...agent.configuration, ...newConfig }
        
        // Save to configuration manager
        this.configurationManager.saveConfiguration(agentId, newConfig)
        
        // Update registry
        this.agentRegistry.updateAgent(agent)
        
        // Show success notification
        this.showNotification({
            type: 'success',
            message: 'Configuration saved successfully'
        })
        
        // Emit configuration change event
        this.emitAgentEvent('configurationChanged', {
            agentId,
            configuration: newConfig,
            timestamp: new Date()
        })
    }
}
```

## Agent Base Classes

```typescript
// TEST: Base agent class provides common functionality
abstract class BaseTradingAgent implements TradingAgent {
    protected agentId: string
    protected name: string
    protected description: string
    protected autonomyLevel: AutonomyLevel
    protected capabilities: AgentCapability[]
    protected riskParameters: RiskParameters
    protected status: AgentStatus
    protected configuration: AgentConfiguration
    protected performance: AgentPerformance
    
    constructor(config: AgentConfig) {
        this.agentId = config.agentId
        this.name = config.name
        this.description = config.description
        this.autonomyLevel = config.autonomyLevel
        this.capabilities = config.capabilities
        this.riskParameters = config.riskParameters
        this.status = AgentStatus.INACTIVE
        this.performance = new AgentPerformance()
    }
    
    // TEST: Agent start process works correctly
    abstract start(): Promise<void>
    
    // TEST: Agent stop process works correctly
    abstract stop(): Promise<void>
    
    // TEST: Agent configuration updates correctly
    abstract configure(config: AgentConfiguration): Promise<void>
    
    // TEST: Agent generates signals correctly
    abstract generateSignal(marketData: MarketData): Promise<TradingSignal>
}
```

## Type Definitions

```typescript
interface AgentConfig {
    agentId: string
    name: string
    description: string
    autonomyLevel: AutonomyLevel
    capabilities: AgentCapability[]
    riskParameters: RiskParameters
}

interface AgentConfiguration {
    riskParameters: RiskParameters
    tradingPreferences: TradingPreferences
    notificationSettings: NotificationSettings
}

interface RiskParameters {
    maxPositionSize: number
    maxDailyLoss: number
    stopLossPercentage: number
    takeProfitPercentage: number
    maxOpenPositions: number
}

enum AutonomyLevel {
    TUTOR = 'tutor',
    SEMI_AUTONOMOUS = 'semi_autonomous',
    AUTONOMOUS = 'autonomous'
}

enum AgentCapability {
    TREND_ANALYSIS = 'trend_analysis',
    TRADE_EXECUTION = 'trade_execution',
    RISK_MANAGEMENT = 'risk_management',
    PORTFOLIO_OPTIMIZATION = 'portfolio_optimization',
    EDUCATIONAL_INSIGHTS = 'educational_insights',
    MARKET_EXPLANATION = 'market_explanation',
    RISK_EDUCATION = 'risk_education',
    PERMISSION_REQUESTS = 'permission_requests',
    ADVANCED_STRATEGIES = 'advanced_strategies',
    MARKET_MAKING = 'market_making',
    ARBITRAGE_DETECTION = 'arbitrage_detection'
}

enum AgentStatus {
    INACTIVE = 'inactive',
    ACTIVE = 'active',
    PAUSED = 'paused',
    ERROR = 'error',
    CONFIGURING = 'configuring'
}