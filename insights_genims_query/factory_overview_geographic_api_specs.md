# Factory Overview - Geographic View: API Specifications

This document provides technical specifications for converting natural language queries into REST API endpoints for the Factory Overview - Geographic View dashboard.

## Core API Endpoints Structure

### Base URL Structure
```
https://api.genims.com/v1/factory-overview/geographic/
```

## 1. Geographic Factory Data APIs

### 1.1 Factory Locations API
**Endpoint**: `GET /factories/locations`

**Natural Language**: "Show me all factory locations with their geographic coordinates, factory names, addresses, and current operational status on a world map"

**Response Schema**:
```json
{
  "status": "success",
  "data": {
    "factories": [
      {
        "factory_id": "FAC-000001",
        "factory_name": "GenIMS Manufacturing Plant 1",
        "coordinates": {
          "latitude": 28.6139,
          "longitude": 77.2090
        },
        "address": {
          "street": "Industrial Area Phase 1",
          "city": "Gurgaon",
          "state": "Haryana",
          "country": "India",
          "postal_code": "122001"
        },
        "operational_status": "active",
        "status_color": "#28a745",
        "establishment_date": "2018-03-15",
        "total_area_sqm": 50000,
        "production_lines_count": 8,
        "current_workforce": 485
      }
    ],
    "metadata": {
      "total_factories": 4,
      "active_factories": 4,
      "last_updated": "2026-01-08T10:15:00Z"
    }
  }
}
```

### 1.2 Factory Performance Heatmap API
**Endpoint**: `GET /factories/performance-heatmap`

**Natural Language**: "Show production efficiency and performance metrics for each factory as a heatmap overlay"

**Query Parameters**:
- `metric`: efficiency|quality|oee|safety
- `period`: today|week|month|quarter
- `comparison`: none|previous_period|same_period_last_year

## 2. Real-time Production Monitoring APIs

### 2.1 Live Production Status API
**Endpoint**: `GET /factories/live-status`

**Natural Language**: "Get current operational status of each factory including active production lines, idle machines, maintenance activities, and alert levels"

**Response Schema**:
```json
{
  "status": "success",
  "data": {
    "factories": [
      {
        "factory_id": "FAC-000001",
        "factory_name": "GenIMS Manufacturing Plant 1",
        "live_metrics": {
          "production_lines": {
            "total": 8,
            "active": 7,
            "idle": 1,
            "maintenance": 0
          },
          "current_production_rate": 85.2,
          "target_production_rate": 90.0,
          "efficiency_percentage": 94.7,
          "quality_rate": 98.5,
          "oee_score": 89.2,
          "alert_level": "normal",
          "active_alerts": 2,
          "critical_alerts": 0
        },
        "last_updated": "2026-01-08T10:15:30Z"
      }
    ]
  }
}
```

### 2.2 Production Trends API
**Endpoint**: `GET /factories/production-trends`

**Natural Language**: "Get the last 7 days of production data for each factory showing daily output trends, quality metrics, and downtime hours"

**Query Parameters**:
- `days`: 1|7|30 (default: 7)
- `granularity`: hourly|daily (default: daily)
- `metrics`: production|quality|downtime|efficiency (comma-separated)

## 3. Comparative Analytics APIs

### 3.1 Factory Benchmarking API
**Endpoint**: `GET /factories/benchmarking`

**Natural Language**: "Compare key performance indicators across all factory locations including production efficiency, quality, costs, and safety metrics"

**Response Schema**:
```json
{
  "status": "success",
  "data": {
    "benchmark_metrics": [
      {
        "metric_name": "Production Efficiency",
        "unit": "percentage",
        "factories": [
          {
            "factory_id": "FAC-000001",
            "factory_name": "Plant 1",
            "value": 94.7,
            "rank": 1,
            "performance_tier": "excellent"
          }
        ],
        "industry_average": 87.3,
        "best_practice_value": 96.2
      }
    ]
  }
}
```

### 3.2 Regional Performance API
**Endpoint**: `GET /factories/regional-analysis`

**Natural Language**: "Analyze performance trends by geographic region, identifying regional strengths and improvement opportunities"

## 4. Resource & Operational APIs

### 4.1 Resource Utilization API
**Endpoint**: `GET /factories/resource-utilization`

**Natural Language**: "Show machine and equipment utilization rates, capacity utilization, and idle time analysis for each factory location"

**Query Parameters**:
- `resource_type`: machines|workforce|energy|materials
- `time_range`: today|week|month
- `breakdown`: detailed|summary

### 4.2 Energy Consumption API
**Endpoint**: `GET /factories/energy-consumption`

**Natural Language**: "Show energy consumption patterns, costs, and efficiency metrics for each factory location with comparison to targets"

## 5. Quality & Safety APIs

### 5.1 Quality Metrics API
**Endpoint**: `GET /factories/quality-metrics`

**Natural Language**: "Show quality metrics for each factory location including defect rates, first-pass yield, customer complaints, and quality score trends"

### 5.2 Safety Dashboard API
**Endpoint**: `GET /factories/safety-metrics`

**Natural Language**: "Get safety incident reports, near-miss events, and safety scores for each factory location over the past month"

## 6. Supply Chain & Logistics APIs

### 6.1 Material Flow API
**Endpoint**: `GET /factories/material-flow`

**Natural Language**: "Display material transfers, components flow, and logistics connections between different factory locations"

**Response Schema**:
```json
{
  "status": "success",
  "data": {
    "material_flows": [
      {
        "source_factory": "FAC-000001",
        "destination_factory": "FAC-000002",
        "material_type": "Component A",
        "quantity": 1500,
        "unit": "pieces",
        "shipment_date": "2026-01-08",
        "estimated_arrival": "2026-01-10",
        "status": "in_transit",
        "flow_color": "#007bff"
      }
    ],
    "flow_connections": [
      {
        "from_coordinates": [28.6139, 77.2090],
        "to_coordinates": [19.0760, 72.8777],
        "flow_volume": "high",
        "flow_status": "active"
      }
    ]
  }
}
```

### 6.2 Inventory Status API
**Endpoint**: `GET /factories/inventory-status`

**Natural Language**: "Get current inventory levels, stock turnover rates, and warehouse capacity utilization for each factory location"

## 7. Financial Performance APIs

### 7.1 Cost Analysis API
**Endpoint**: `GET /factories/cost-analysis`

**Natural Language**: "Show production costs, cost per unit, and cost efficiency trends for each factory location over the past quarter"

### 7.2 Revenue Performance API
**Endpoint**: `GET /factories/revenue-performance`

**Natural Language**: "Get revenue generated, profit margins, and return on investment for each factory location"

## 8. Predictive Analytics APIs

### 8.1 Production Forecast API
**Endpoint**: `GET /factories/production-forecast`

**Natural Language**: "Get production forecasts for the next 30 days for each factory location based on historical trends and current capacity"

**Query Parameters**:
- `forecast_days`: 7|15|30|60|90 (default: 30)
- `confidence_level`: 80|90|95 (default: 90)
- `include_scenarios`: true|false (default: false)

### 8.2 Predictive Maintenance API
**Endpoint**: `GET /factories/predictive-maintenance`

**Natural Language**: "Get predictive maintenance recommendations and equipment failure predictions for critical assets across all factories"

## 9. Alert & Notification APIs

### 9.1 Active Alerts API
**Endpoint**: `GET /factories/active-alerts`

**Natural Language**: "Get all active alerts, alarms, and critical issues across factory locations categorized by severity level and department"

**Response Schema**:
```json
{
  "status": "success",
  "data": {
    "alerts": [
      {
        "alert_id": "ALT-20260108-001",
        "factory_id": "FAC-000001",
        "severity": "high",
        "category": "production",
        "title": "Production Line 3 Efficiency Drop",
        "description": "Efficiency dropped below 85% threshold",
        "timestamp": "2026-01-08T09:45:00Z",
        "status": "active",
        "estimated_impact": "medium",
        "recommended_action": "Check conveyor belt tension"
      }
    ],
    "summary": {
      "total_alerts": 12,
      "critical": 1,
      "high": 3,
      "medium": 5,
      "low": 3
    }
  }
}
```

## 10. Executive Dashboard APIs

### 10.1 Executive Summary API
**Endpoint**: `GET /factories/executive-summary`

**Natural Language**: "Provide executive-level summary including overall factory performance, key metrics, critical issues, and strategic recommendations by location"

### 10.2 KPI Dashboard API
**Endpoint**: `GET /factories/kpi-dashboard`

**Natural Language**: "Display strategic KPIs including overall equipment effectiveness, quality index, cost efficiency, and safety performance by factory"

## Common Request/Response Patterns

### Standard Query Parameters
- `time_range`: today|yesterday|week|month|quarter|year|custom
- `start_date`: YYYY-MM-DD (for custom range)
- `end_date`: YYYY-MM-DD (for custom range)
- `factory_ids`: comma-separated list of factory IDs
- `format`: json|csv|excel
- `include_metadata`: true|false
- `aggregation`: sum|avg|min|max|count

### Standard Error Response
```json
{
  "status": "error",
  "error": {
    "code": "INVALID_PARAMETER",
    "message": "Invalid time_range parameter",
    "details": "time_range must be one of: today, week, month, quarter, year, custom"
  }
}
```

### Rate Limiting Headers
```
X-RateLimit-Limit: 1000
X-RateLimit-Remaining: 999
X-RateLimit-Reset: 1641658800
```

## WebSocket APIs for Real-time Updates

### Factory Status Updates
**Endpoint**: `wss://api.genims.com/v1/ws/factory-overview/live-updates`

**Subscription Message**:
```json
{
  "action": "subscribe",
  "channels": ["factory_status", "production_metrics", "alerts"],
  "factory_ids": ["FAC-000001", "FAC-000002"]
}
```

**Live Update Message**:
```json
{
  "channel": "factory_status",
  "factory_id": "FAC-000001",
  "timestamp": "2026-01-08T10:16:00Z",
  "data": {
    "production_rate": 87.3,
    "efficiency": 95.1,
    "quality_rate": 98.7,
    "alert_count": 1
  }
}
```

## Authentication & Security

### API Authentication
```http
Authorization: Bearer <jwt_token>
X-API-Key: <api_key>
```

### Required Permissions
- `factory:read` - Read factory data
- `production:read` - Read production metrics
- `analytics:read` - Read analytics data
- `alerts:read` - Read alert information

## Implementation Notes

1. **Caching Strategy**: Implement Redis caching for frequently accessed data
2. **Database Optimization**: Use read replicas for analytics queries
3. **Response Compression**: Enable gzip compression for large responses
4. **Monitoring**: Implement comprehensive API monitoring and logging
5. **Documentation**: Maintain OpenAPI/Swagger documentation
6. **Versioning**: Use semantic versioning for API changes