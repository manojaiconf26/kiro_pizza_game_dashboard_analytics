# API Setup Guide for Pizza Game Dashboard

This guide explains how to set up external API access for the Pizza Game Dashboard.

## Football Data API Setup

### 1. Get Your API Key

1. Visit [football-data.org](https://www.football-data.org/client/register)
2. Register for a free account
3. Copy your API key from the dashboard

### 2. Free Tier Limits

The free tier includes:
- **10 requests per minute**
- **Access to Premier League data**
- **Completed matches only**

### 3. Environment Variable Configuration

#### For Local Development

**Windows:**
```cmd
set FOOTBALL_API_KEY=your_api_key_here
```

**Linux/Mac:**
```bash
export FOOTBALL_API_KEY=your_api_key_here
```

#### For Lambda Deployment

The API key is configured through the SAM template parameters:

```bash
sam deploy --parameter-overrides FootballApiKey=your_api_key_here
```

Or update the `template.yaml` parameters section.

### 4. Testing Your Setup

Run the example script to test your API configuration:

```bash
python example_usage.py
```

This will:
- ✅ Test your API key
- 📊 Collect recent football matches
- 🍕 Generate mock pizza orders
- 📋 Show sample data

## Domino's API (Optional)

Currently, the Domino's API integration is prepared but uses mock data by default since:
- Real Domino's APIs require business partnerships
- Mock data provides realistic patterns for analysis

If you have access to Domino's APIs:
1. Set `DOMINOS_API_KEY` environment variable
2. Set `DOMINOS_STORE_ID` environment variable
3. The system will automatically use real data

## Environment Variables Reference

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `FOOTBALL_API_KEY` | football-data.org API key | None | No* |
| `DOMINOS_API_KEY` | Domino's API key | None | No |
| `DOMINOS_STORE_ID` | Domino's store ID | None | No |
| `MAX_REQUESTS_PER_MINUTE` | API rate limit | 60 | No |
| `MAX_REQUESTS_PER_HOUR` | API hourly limit | 1000 | No |
| `S3_BUCKET_NAME` | S3 bucket for data storage | pizza-game-analytics-default | Yes |

*If no API key is provided, the system will use mock data

## Fallback Behavior

The system is designed to work without API keys:

1. **With API Key**: Collects real football data from football-data.org
2. **Without API Key**: Generates realistic mock football data
3. **API Failures**: Automatically falls back to mock data
4. **Rate Limits**: Respects API limits and waits when necessary

## Lambda Configuration

When deploying to AWS Lambda, the environment variables are automatically configured through the SAM template:

```yaml
Environment:
  Variables:
    FOOTBALL_API_KEY: !Ref FootballApiKey
    DOMINOS_API_KEY: !Ref DominosApiKey
    # ... other variables
```

## Troubleshooting

### Common Issues

1. **"No API key" warnings**: Normal if you haven't set up the API key yet
2. **Rate limit errors**: The system will automatically wait and retry
3. **Network timeouts**: The system will fall back to mock data
4. **Invalid API key**: Check your key at football-data.org

### Checking Your Configuration

```python
from src.data_collection import create_api_config_from_env

config = create_api_config_from_env()
print(f"Football API Key: {'Set' if config.football_api_key else 'Not set'}")
```

## Next Steps

Once your API is configured:
1. The Lambda function will automatically collect real football data
2. Mock pizza orders will be generated with realistic patterns
3. Data will be stored in S3 for analysis
4. QuickSight dashboards will show correlations between matches and orders

For questions or issues, check the logs in CloudWatch when running in Lambda.