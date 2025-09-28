# iwhereGIS Grid Engine API Documentation

## Version: 2.0.0

## Base URL
```
https://api.iwheregis.com/api/v1
```

## Authentication

### API Key Authentication
Include your API key in the request header:
```
X-API-Key: your-api-key-here
```

Or as a query parameter:
```
?api_key=your-api-key-here
```

## Rate Limiting

- **Default Rate Limit**: 100 requests per hour
- **Rate Limit Headers**:
  - `X-RateLimit-Limit`: Maximum requests allowed
  - `X-RateLimit-Remaining`: Requests remaining
  - `X-RateLimit-Reset`: Time when limit resets (Unix timestamp)

## Response Format

All responses are in JSON format with the following structure:

### Success Response
```json
{
  "success": true,
  "message": "Operation completed successfully",
  "data": {
    // Response data
  }
}
```

### Error Response
```json
{
  "error": "Error message",
  "code": "ERROR_CODE",
  "details": {
    // Additional error details
  }
}
```

## Error Codes

| Code | Description |
|------|-------------|
| `VALIDATION_ERROR` | Input validation failed |
| `GRID_NOT_FOUND` | Grid not found |
| `GRID_GENERATION_ERROR` | Grid generation failed |
| `ATTRIBUTE_ERROR` | Attribute operation failed |
| `ROUTE_CALCULATION_ERROR` | Route calculation failed |
| `AUTHENTICATION_ERROR` | Authentication failed |
| `RATE_LIMIT_ERROR` | Rate limit exceeded |
| `INTERNAL_ERROR` | Internal server error |

## Endpoints

### 1. Health & Status

#### GET /health
Check service health status.

**Response:**
```json
{
  "status": "healthy",
  "service": "iwhereGIS Grid Engine",
  "version": "2.0.0",
  "environment": "production",
  "timestamp": "2024-01-01T00:00:00Z"
}
```

#### GET /status
Get detailed service status (requires authentication).

**Response:**
```json
{
  "status": "operational",
  "service": "iwhereGIS Grid Engine",
  "version": "2.0.0",
  "environment": "production",
  "statistics": {
    "total_grids": 1000,
    "level_distribution": {
      "8": 500,
      "10": 300,
      "12": 200
    }
  },
  "features": {
    "visualization": true,
    "risk_assessment": true,
    "route_planning": true
  },
  "timestamp": "2024-01-01T00:00:00Z"
}
```

### 2. Grid Generation

#### POST /grids/generate
Generate grids for a specified area.

**Request Body:**
```json
{
  "lon_min": 114.0,
  "lon_max": 114.001,
  "lat_min": 22.5,
  "lat_max": 22.501,
  "level": 8,
  "alt_min": 0,
  "alt_max": 100
}
```

**Parameters:**
- `lon_min` (required, float): Minimum longitude (-180 to 180)
- `lon_max` (required, float): Maximum longitude (-180 to 180)
- `lat_min` (required, float): Minimum latitude (-90 to 90)
- `lat_max` (required, float): Maximum latitude (-90 to 90)
- `level` (required, int): Grid level (1-16)
- `alt_min` (optional, float): Minimum altitude in meters (default: 0)
- `alt_max` (optional, float): Maximum altitude in meters (default: 1000)

**Response:**
```json
{
  "success": true,
  "message": "Successfully generated 42 grids",
  "data": {
    "grids": [
      {
        "code": "L8:114.000:22.500:0",
        "level": 8,
        "bbox": [114.0, 22.5, 114.001, 22.501],
        "center": [114.0005, 22.5005],
        "size": [0.001, 0.001],
        "alt_range": [0, 100]
      }
    ],
    "count": 42,
    "parameters": {
      "bbox": [114.0, 22.5, 114.001, 22.501],
      "level": 8,
      "alt_range": [0, 100]
    }
  }
}
```

### 3. Grid Query

#### GET /grids/{grid_code}
Get grid information by code.

**Path Parameters:**
- `grid_code` (string): Grid code

**Response:**
```json
{
  "success": true,
  "data": {
    "code": "L8:114.000:22.500:0",
    "level": 8,
    "bbox": [114.0, 22.5, 114.001, 22.501],
    "center": [114.0005, 22.5005],
    "size": [0.001, 0.001],
    "alt_range": [0, 100]
  }
}
```

### 4. Coordinate Encoding

#### POST /grids/encode
Encode coordinates to grid code.

**Request Body:**
```json
{
  "lon": 114.1234,
  "lat": 22.5678,
  "alt": 100,
  "level": 8
}
```

**Parameters:**
- `lon` (required, float): Longitude (-180 to 180)
- `lat` (required, float): Latitude (-90 to 90)
- `alt` (optional, float): Altitude in meters (default: 0)
- `level` (required, int): Grid level (1-16)

**Response:**
```json
{
  "success": true,
  "data": {
    "grid_code": "L8:114.123:22.567:100",
    "coordinates": {
      "lon": 114.1234,
      "lat": 22.5678,
      "alt": 100
    },
    "level": 8
  }
}
```

### 5. Attribute Management

#### GET /grids/{grid_code}/attributes
Get grid attributes.

**Path Parameters:**
- `grid_code` (string): Grid code

**Response:**
```json
{
  "success": true,
  "data": {
    "grid_code": "L8:114.000:22.500:0",
    "flight_rules": {
      "max_altitude": 500,
      "min_altitude": 50,
      "speed_limit": 100
    },
    "airspace_status": {
      "restricted": false,
      "type": "unrestricted"
    },
    "weather_conditions": {
      "visibility": "good",
      "wind_speed": 10
    },
    "risk_assessment": {
      "risk_level": "low",
      "score": 2
    }
  }
}
```

#### PUT /grids/{grid_code}/attributes
Update grid attributes.

**Path Parameters:**
- `grid_code` (string): Grid code

**Request Body:**
```json
{
  "category": "flight_rules",
  "key": "max_altitude",
  "value": 500
}
```

**Parameters:**
- `category` (required, string): Attribute category
  - Options: `flight_rules`, `airspace_status`, `weather_conditions`, `risk_assessment`, `custom`
- `key` (required, string): Attribute key
- `value` (required, any): Attribute value

**Response:**
```json
{
  "success": true,
  "message": "Attribute updated successfully",
  "data": {
    "grid_code": "L8:114.000:22.500:0",
    "category": "flight_rules",
    "key": "max_altitude",
    "value": 500
  }
}
```

### 6. Search

#### POST /grids/search
Search grids by attributes.

**Request Body:**
```json
{
  "category": "risk_assessment",
  "key": "risk_level",
  "value": "high"
}
```

**Parameters:**
- `category` (required, string): Attribute category
- `key` (required, string): Attribute key
- `value` (required, any): Attribute value to search for

**Response:**
```json
{
  "success": true,
  "data": {
    "grids": [
      {
        "code": "L8:114.000:22.500:0",
        "level": 8,
        "bbox": [114.0, 22.5, 114.001, 22.501],
        "center": [114.0005, 22.5005]
      }
    ],
    "count": 5,
    "search_criteria": {
      "category": "risk_assessment",
      "key": "risk_level",
      "value": "high"
    }
  }
}
```

### 7. Route Planning

#### POST /grids/route
Calculate grids along a route.

**Request Body:**
```json
{
  "waypoints": [
    [114.05, 22.55, 100],
    [114.06, 22.56, 120],
    [114.07, 22.57, 150]
  ],
  "level": 8
}
```

**Parameters:**
- `waypoints` (required, array): List of waypoint coordinates `[lon, lat, alt]`
  - Minimum 2 waypoints
  - Maximum 100 waypoints
- `level` (optional, int): Grid level (1-16, default: 8)

**Response:**
```json
{
  "success": true,
  "data": {
    "grid_codes": [
      "L8:114.050:22.550:100",
      "L8:114.055:22.555:110",
      "L8:114.060:22.560:120"
    ],
    "route_grids": [
      {
        "code": "L8:114.050:22.550:100",
        "level": 8,
        "bbox": [114.05, 22.55, 114.051, 22.551],
        "center": [114.0505, 22.5505],
        "alt_range": [100, 110],
        "size": [0.001, 0.001]
      }
    ],
    "count": 15,
    "waypoints": [[114.05, 22.55, 100], [114.06, 22.56, 120], [114.07, 22.57, 150]],
    "level": 8
  }
}
```

### 8. Risk Assessment

#### GET /grids/{grid_code}/risk
Get risk assessment for a grid.

**Path Parameters:**
- `grid_code` (string): Grid code

**Response:**
```json
{
  "success": true,
  "data": {
    "grid_code": "L8:114.000:22.500:0",
    "risk_level": 2,
    "risk_category": "low"
  }
}
```

**Risk Categories:**
- `1`: very_low
- `2`: low
- `3`: medium
- `4`: high
- `5`: very_high

### 9. Statistics

#### GET /statistics
Get system statistics.

**Response:**
```json
{
  "success": true,
  "data": {
    "total_grids": 10000,
    "level_distribution": {
      "6": 100,
      "8": 5000,
      "10": 3000,
      "12": 1900
    }
  }
}
```

### 10. Routes Data

#### GET /routes
Get available predefined routes.

**Response:**
```json
{
  "success": true,
  "data": {
    "routes": [
      {
        "id": "route_001",
        "name": "Shenzhen Bay Route",
        "points": [
          [114.05, 22.55, 100],
          [114.06, 22.56, 120],
          [114.07, 22.57, 150]
        ],
        "metadata": {
          "created_at": "2024-01-01T00:00:00Z",
          "updated_at": "2024-01-01T00:00:00Z"
        }
      }
    ],
    "count": 1
  }
}
```

## Examples

### Python Example
```python
import requests

# Configuration
API_BASE_URL = "https://api.iwheregis.com/api/v1"
API_KEY = "your-api-key"

headers = {
    "X-API-Key": API_KEY,
    "Content-Type": "application/json"
}

# Generate grids
payload = {
    "lon_min": 114.0,
    "lon_max": 114.001,
    "lat_min": 22.5,
    "lat_max": 22.501,
    "level": 8
}

response = requests.post(
    f"{API_BASE_URL}/grids/generate",
    json=payload,
    headers=headers
)

if response.status_code == 200:
    data = response.json()
    print(f"Generated {data['data']['count']} grids")
else:
    print(f"Error: {response.json()}")
```

### JavaScript Example
```javascript
const API_BASE_URL = 'https://api.iwheregis.com/api/v1';
const API_KEY = 'your-api-key';

// Generate grids
async function generateGrids() {
    const payload = {
        lon_min: 114.0,
        lon_max: 114.001,
        lat_min: 22.5,
        lat_max: 22.501,
        level: 8
    };

    const response = await fetch(`${API_BASE_URL}/grids/generate`, {
        method: 'POST',
        headers: {
            'X-API-Key': API_KEY,
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(payload)
    });

    if (response.ok) {
        const data = await response.json();
        console.log(`Generated ${data.data.count} grids`);
    } else {
        const error = await response.json();
        console.error('Error:', error);
    }
}

generateGrids();
```

### cURL Example
```bash
# Generate grids
curl -X POST https://api.iwheregis.com/api/v1/grids/generate \
  -H "X-API-Key: your-api-key" \
  -H "Content-Type: application/json" \
  -d '{
    "lon_min": 114.0,
    "lon_max": 114.001,
    "lat_min": 22.5,
    "lat_max": 22.501,
    "level": 8
  }'

# Get grid by code
curl -X GET https://api.iwheregis.com/api/v1/grids/L8:114.000:22.500:0 \
  -H "X-API-Key: your-api-key"

# Calculate route
curl -X POST https://api.iwheregis.com/api/v1/grids/route \
  -H "X-API-Key: your-api-key" \
  -H "Content-Type: application/json" \
  -d '{
    "waypoints": [
      [114.05, 22.55, 100],
      [114.06, 22.56, 120],
      [114.07, 22.57, 150]
    ],
    "level": 8
  }'
```

## Webhooks

### Event Types
- `grid.created`: Grid created
- `grid.updated`: Grid attributes updated
- `route.calculated`: Route calculation completed

### Webhook Payload
```json
{
  "event": "grid.created",
  "timestamp": "2024-01-01T00:00:00Z",
  "data": {
    // Event-specific data
  }
}
```

## SDKs

Official SDKs are available for:
- Python: `pip install iwheregis-python`
- JavaScript/Node.js: `npm install @iwheregis/sdk`
- Go: `go get github.com/iwheregis/go-sdk`
- Java: Maven/Gradle packages available

## Support

- **Documentation**: https://docs.iwheregis.com
- **API Status**: https://status.iwheregis.com
- **Support Email**: api-support@iwheregis.com
- **GitHub**: https://github.com/iwheregis/grid-engine

## Changelog

### v2.0.0 (2024-01-01)
- Complete API redesign
- Added authentication and rate limiting
- Improved error handling
- Added risk assessment endpoints
- Performance optimizations

### v1.0.0 (2023-01-01)
- Initial release
- Basic grid generation and query
- Attribute management
- Route planning