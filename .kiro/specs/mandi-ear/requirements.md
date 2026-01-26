# Requirements Document: MANDI EAR™

## Introduction

MANDI EAR™ is India's first ambient AI-powered, farmer-first, multilingual national trade and farming intelligence platform. The system transforms ambient market conversations, real-time signals, and national data streams into a live agricultural intelligence network. The platform empowers farmers and local vendors with real-time price discovery, AI-driven negotiation assistance, intelligent crop planning, MSP enforcement, and cross-state market visibility — all delivered in 50+ Indian languages via voice and text interfaces.

## Glossary

- **MANDI_EAR**: The complete agricultural intelligence platform system
- **Ambient_AI_Engine**: AI system that passively processes ambient conversations to extract market intelligence
- **Price_Discovery_System**: Real-time price intelligence extraction and processing subsystem
- **Negotiation_Copilot**: AI assistant that provides real-time negotiation guidance
- **Crop_Planning_Engine**: AI system for pre-sowing crop and income planning recommendations
- **MSP_Enforcement_Engine**: System for tracking and enforcing Minimum Support Price compliance
- **Voice_Interface**: Multilingual voice processing and response system
- **Cross_Mandi_Network**: National network of mandi price data and intelligence
- **Anti_Hoarding_Detector**: System for detecting artificial price manipulation and hoarding patterns
- **Farmer**: Primary end user - agricultural producers using the platform
- **Vendor**: Local agricultural traders and middlemen
- **Mandi**: Traditional Indian agricultural marketplace
- **MSP**: Minimum Support Price - government-set minimum price for agricultural commodities
- **FPO**: Farmer Producer Organization

## Requirements

### Requirement 1: Ambient AI Price Discovery

**User Story:** As a farmer, I want the system to automatically capture and process price conversations happening around me in the mandi, so that I can access real-time market intelligence without manual data entry.

#### Acceptance Criteria

1. WHEN ambient audio contains commodity price discussions, THE Ambient_AI_Engine SHALL extract commodity name, price, quantity, and location data with 85% accuracy
2. WHEN processing ambient conversations, THE Price_Discovery_System SHALL identify speaker intent (buying/selling) and urgency levels
3. WHEN multiple price points are mentioned for the same commodity, THE System SHALL calculate weighted average prices based on quantity and recency
4. WHEN ambient data is processed, THE System SHALL timestamp and geo-tag all price intelligence within 30 seconds of capture
5. WHEN background noise exceeds 70dB, THE Ambient_AI_Engine SHALL maintain minimum 75% extraction accuracy

### Requirement 2: Multilingual Voice and Text Interface

**User Story:** As a farmer who speaks regional languages, I want to interact with the platform using voice commands and receive responses in my native language, so that language barriers don't prevent me from accessing market intelligence.

#### Acceptance Criteria

1. THE Voice_Interface SHALL support voice input and output in 50+ Indian languages including Hindi, Tamil, Telugu, Bengali, Marathi, Gujarati, Kannada, Malayalam, Punjabi, and Odia
2. WHEN a user speaks a query, THE System SHALL process voice input and respond within 3 seconds
3. WHEN providing price information, THE Voice_Interface SHALL use local currency denominations and measurement units familiar to the user's region
4. WHEN language detection is uncertain, THE System SHALL ask for clarification in the most likely detected language
5. THE System SHALL maintain conversation context across multiple voice interactions within a 10-minute session

### Requirement 3: Real-Time National Cross-Mandi Price Visibility

**User Story:** As a farmer, I want to see live prices from mandis across all Indian states, so that I can identify the best markets to sell my produce and maximize my income.

#### Acceptance Criteria

1. THE Cross_Mandi_Network SHALL display real-time prices from mandis across all 28 Indian states and 8 union territories
2. WHEN a user queries commodity prices, THE System SHALL return prices from minimum 5 different mandis within 500km radius
3. WHEN displaying cross-mandi prices, THE System SHALL include transportation costs and net profit calculations
4. THE System SHALL update mandi prices every 15 minutes during market hours (6 AM to 8 PM IST)
5. WHEN mandi data is unavailable, THE System SHALL indicate data freshness and provide estimated prices based on historical trends

### Requirement 4: AI Negotiation Copilot

**User Story:** As a farmer negotiating with buyers, I want real-time guidance on pricing strategies and market conditions, so that I can secure better prices for my produce.

#### Acceptance Criteria

1. WHEN a negotiation session begins, THE Negotiation_Copilot SHALL provide real-time price benchmarks based on current market conditions
2. WHEN buyer intent signals are detected, THE System SHALL suggest optimal counter-offers within 5 seconds
3. WHEN market demand is high, THE Negotiation_Copilot SHALL recommend holding strategies with time-based price predictions
4. THE System SHALL track negotiation outcomes and learn from successful pricing strategies for future recommendations
5. WHEN multiple buyers are present, THE Negotiation_Copilot SHALL facilitate competitive bidding scenarios

### Requirement 5: Intelligent Crop Planning Engine

**User Story:** As a farmer planning my next crop cycle, I want AI-powered recommendations considering weather, soil, demand, and market trends, so that I can maximize my income and minimize risks.

#### Acceptance Criteria

1. WHEN planning season begins, THE Crop_Planning_Engine SHALL analyze weather forecasts, soil conditions, national demand patterns, and historical trends
2. THE System SHALL provide crop recommendations with expected income projections and risk assessments
3. WHEN festival calendars affect demand, THE Crop_Planning_Engine SHALL factor seasonal demand spikes into recommendations
4. THE System SHALL consider export demand patterns and international market trends for high-value crops
5. WHEN water availability is limited, THE Crop_Planning_Engine SHALL prioritize drought-resistant crops with optimal water usage

### Requirement 6: MSP Protection and Enforcement Engine

**User Story:** As a farmer, I want continuous monitoring of market prices against government MSP rates with alerts and alternative market suggestions, so that I never sell below the guaranteed minimum price.

#### Acceptance Criteria

1. THE MSP_Enforcement_Engine SHALL continuously compare real-time mandi prices against official MSP rates for all covered commodities
2. WHEN mandi prices fall below MSP, THE System SHALL immediately alert farmers and suggest alternative procurement centers
3. THE System SHALL maintain updated MSP rates for all seasons and commodities as announced by the government
4. WHEN MSP violations are detected, THE MSP_Enforcement_Engine SHALL generate reports for regulatory authorities
5. THE System SHALL provide directions and contact information for government procurement centers accepting MSP rates

### Requirement 7: Supply-Demand Optimization and Anti-Hoarding Detection

**User Story:** As a farmer and market participant, I want the system to detect artificial price manipulation and hoarding patterns, so that I can make informed decisions in a fair market environment.

#### Acceptance Criteria

1. THE Anti_Hoarding_Detector SHALL identify unusual price spikes that deviate more than 25% from 30-day moving averages
2. WHEN supply chain manipulation is detected, THE System SHALL alert farmers about artificial scarcity and suggest alternative markets
3. THE System SHALL track inventory levels across major mandis and detect abnormal stockpiling patterns
4. WHEN hoarding patterns are identified, THE Anti_Hoarding_Detector SHALL notify relevant authorities and provide evidence reports
5. THE System SHALL provide supply-demand balance indicators for each commodity across different regions

### Requirement 8: Vendor and Farmer Self-Benchmarking

**User Story:** As a farmer, I want to track price conversations, build local benchmarks, and set minimum selling price floors, so that I can eliminate middleman dependency and improve my negotiating position.

#### Acceptance Criteria

1. THE System SHALL allow farmers to set personalized minimum selling price floors based on production costs and profit targets
2. WHEN price conversations are captured, THE System SHALL build historical price benchmarks for each farmer's local market
3. THE System SHALL track farmer's selling performance against local and regional benchmarks
4. WHEN prices fall below farmer's set floor, THE System SHALL suggest alternative buyers or markets
5. THE System SHALL provide performance analytics showing income improvement over time

### Requirement 9: Real-Time Data Processing and Alerts

**User Story:** As a farmer, I want instant notifications about price changes, market opportunities, and critical updates, so that I can act quickly on time-sensitive market conditions.

#### Acceptance Criteria

1. THE System SHALL process and analyze incoming data streams within 30 seconds of receipt
2. WHEN significant price movements occur (>10% change), THE System SHALL send immediate alerts to affected farmers
3. THE System SHALL provide customizable alert thresholds for different commodities and market conditions
4. WHEN weather emergencies affect crops, THE System SHALL send targeted alerts with actionable recommendations
5. THE System SHALL maintain 99.5% uptime during critical market hours (6 AM to 8 PM IST)

### Requirement 10: Platform Accessibility and User Experience

**User Story:** As a farmer with varying levels of digital literacy, I want an intuitive interface that works on both mobile and web platforms, so that I can easily access all platform features regardless of my technical skills.

#### Acceptance Criteria

1. THE MANDI_EAR SHALL provide identical functionality across web browsers and mobile applications (Android/iOS)
2. THE System SHALL support offline mode for basic price queries and cached data access
3. WHEN internet connectivity is poor, THE System SHALL optimize data usage and provide essential information first
4. THE System SHALL provide tutorial modes and guided onboarding for new users
5. WHEN accessibility features are needed, THE System SHALL support screen readers and high-contrast modes for visually impaired users