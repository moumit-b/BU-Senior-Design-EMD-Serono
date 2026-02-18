# Configuration Selection Feature

## Overview

The application now supports **dual configuration modes** allowing users to choose between:

1. **Standard Configuration** - Open-source using Anthropic Claude Sonnet 4.5
2. **Merck Enterprise Configuration** - Enterprise using Azure OpenAI and AWS Bedrock

## How to Use

### 1. Launch the Application

```bash
cd streamlit-app
streamlit run app.py
```

### 2. Select Configuration

In the sidebar, use the **"Select Configuration"** dropdown to choose:

- **Standard Configuration** - Uses `config.py`
- **Merck Enterprise Configuration** - Uses `config_merck.py`

### 3. Environment Setup

#### For Standard Configuration:
```bash
# Set in .env file or environment
ANTHROPIC_API_KEY=sk-ant-api03-your-key-here
```

#### For Merck Enterprise Configuration:
```bash
# Set in .env file or environment  
AZURE_OPENAI_API_KEY=your-azure-key-here
# OR
AZURE_API_KEY=your-azure-key-here
```

## Configuration Details

### Standard Configuration (config.py)
- **LLM Provider**: Anthropic Claude Sonnet 4.5
- **MCP Servers**: PubChem, BioMCP, Literature, Data Analysis, Web Knowledge
- **Use Case**: Open-source pharmaceutical research
- **Organization**: BU Senior Design

### Merck Enterprise Configuration (config_merck.py)
- **LLM Providers**: 
  - Azure OpenAI (GPT-4o, GPT-4-turbo, GPT-3.5-turbo-16k)
  - AWS Bedrock (Claude 3.5 Sonnet, Claude 3 Sonnet/Haiku)
- **MCP Servers**: None (Direct LLM mode)
- **Use Case**: Enterprise vendor analysis and research intelligence
- **Organization**: Merck R&D
- **Additional Features**: Video analysis, scoring system, enterprise compliance

## Technical Implementation

### Files Created/Modified:

1. **`config_manager.py`** - Dynamic configuration loading
2. **`utils/llm_factory.py`** - Enhanced to support Azure OpenAI and Bedrock
3. **`agent.py`** - Updated to accept configuration data
4. **`app.py`** - Added configuration selection UI
5. **`requirements.txt`** - Added Azure OpenAI dependencies

### Key Features:

- **Dynamic Configuration Loading**: Seamlessly switch between configs
- **API Key Validation**: Real-time validation for each configuration
- **UI Adaptation**: Interface changes based on selected configuration
- **Error Handling**: Graceful fallbacks and clear error messages
- **Backward Compatibility**: Existing functionality preserved

## Configuration Architecture

```
User Selection (UI)
        ↓
ConfigurationManager
        ↓
config.py OR config_merck.py
        ↓
Enhanced LLM Factory
        ↓
ChatAnthropic OR AzureChatOpenAI OR ChatOpenAI
        ↓
MCPAgent with appropriate LLM
```

## Usage Examples

### Standard Mode Queries:
- "What is the molecular formula of aspirin?"
- "Find inhibitors of BRCA1" 
- "Explain the mechanism of action of ibuprofen"

### Merck Enterprise Mode Queries:
- "Generate competitive intelligence report on diabetes drugs"
- "Analyze clinical trial trends for immunotherapy"
- "Compare drug efficacy across multiple studies"

## Troubleshooting

### Configuration Not Loading:
- Check that the config file exists (`config.py` or `config_merck.py`)
- Verify Python import path

### API Key Issues:
- **Standard**: Ensure `ANTHROPIC_API_KEY` is set correctly
- **Merck**: Ensure `AZURE_OPENAI_API_KEY` or `AZURE_API_KEY` is set

### LLM Not Ready:
- Check API key format and validity
- Verify network connectivity to LLM endpoints
- Check rate limits and quotas

### Dependencies Missing:
```bash
pip install -r requirements.txt

# If you get langchain-openai import errors when using Merck configuration:
pip install langchain-openai openai
```

## Future Enhancements

1. **Additional Configurations**: Support for more enterprise clients
2. **Model Selection**: UI for choosing specific models within configurations
3. **Configuration Validation**: Pre-flight checks before initialization
4. **Usage Analytics**: Track configuration usage patterns
5. **Configuration Profiles**: Save and load custom configuration profiles

## Security Considerations

- API keys are loaded from environment variables only
- No sensitive data stored in configuration files
- Enterprise endpoints use secure authenticated connections
- Audit logging available for enterprise configurations