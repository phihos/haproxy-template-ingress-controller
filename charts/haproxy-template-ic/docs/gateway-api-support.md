# Gateway API Support

The HAProxy Template Ingress Controller chart provides Gateway API support through the `gateway.yaml` template library. This document describes which features of Gateway API v1.2.0 HTTPRoute and GRPCRoute are currently supported.

## Overview

Gateway API support is implemented as a template library that plugs into the controller's resource-agnostic architecture. The controller itself doesn't know about Gateway API - resource support is added by the chart through template libraries.

**Enable Gateway API support:**

```yaml
# values.yaml
controller:
  templateLibraries:
    gateway:
      enabled: true
```

The Gateway API CRDs must be installed separately in your cluster. The chart automatically detects their presence and enables the gateway library if available.

## Architecture

The `gateway.yaml` library:
- Declares `httproutes` and `grpcroutes` as watched resources
- Implements backend generation for Gateway routes
- Adds routing rules to HAProxy map files
- Plugs into extension points defined in `base.yaml`

This architecture allows the controller to remain resource-agnostic while the chart provides specific resource support.

## HTTPRoute Support

### spec.parentRefs

| Field | Status | Notes |
|-------|--------|-------|
| `parentRefs[].name` | ✅ Supported | Gateway reference |
| `parentRefs[].namespace` | ⚠️ Partial | Field exists but cross-namespace not tested |
| `parentRefs[].sectionName` | ❌ Not Implemented | Listener-specific attachment not supported |
| `parentRefs[].port` | ❌ Not Implemented | Port override not supported |

### spec.hostnames

| Field | Status | Notes |
|-------|--------|-------|
| `hostnames[]` | ✅ Supported | Multiple hostnames per route |
| Wildcard hostnames (e.g., `*.example.com`) | ⚠️ Untested | May work but not validated |
| Empty hostnames list | ✅ Supported | Matches all hosts |

**Example:**

```yaml
apiVersion: gateway.networking.k8s.io/v1
kind: HTTPRoute
metadata:
  name: example
spec:
  hostnames:
    - "example.com"
    - "www.example.com"
  rules:
    - backendRefs:
        - name: example-svc
          port: 80
```

### spec.rules[].matches - Path Matching

| Field | Status | Notes |
|-------|--------|-------|
| `matches[].path.type: Exact` | ✅ Supported | Exact path match using HAProxy map |
| `matches[].path.type: PathPrefix` | ✅ Supported | Prefix match using HAProxy map_beg |
| `matches[].path.type: RegularExpression` | ✅ Supported | Regex match using HAProxy map_reg |
| `matches[].path.value` | ✅ Supported | Path value used in matching |
| Empty matches list | ✅ Supported | Defaults to PathPrefix `/` |

**Path Match Priority:** Exact > Regex > Prefix-exact > Prefix (configurable via libraries)

**Example - Path matching:**

```yaml
spec:
  rules:
    # Exact path match
    - matches:
        - path:
            type: Exact
            value: /api/v1/users
      backendRefs:
        - name: users-api-svc
          port: 8080

    # Prefix match
    - matches:
        - path:
            type: PathPrefix
            value: /api
      backendRefs:
        - name: api-svc
          port: 8080

    # Regex match
    - matches:
        - path:
            type: RegularExpression
            value: ^/api/v[0-9]+/.*
      backendRefs:
        - name: versioned-api-svc
          port: 8080
```

### spec.rules[].matches - Header and Query Matching

| Field | Status | Notes |
|-------|--------|-------|
| `matches[].headers[]` | ❌ Not Implemented | Header-based routing not supported |
| `matches[].headers[].type` | ❌ Not Implemented | Exact/RegularExpression not available |
| `matches[].headers[].name` | ❌ Not Implemented | |
| `matches[].headers[].value` | ❌ Not Implemented | |
| `matches[].queryParams[]` | ❌ Not Implemented | Query parameter matching not supported |
| `matches[].queryParams[].type` | ❌ Not Implemented | |
| `matches[].queryParams[].name` | ❌ Not Implemented | |
| `matches[].queryParams[].value` | ❌ Not Implemented | |

### spec.rules[].filters

| Filter Type | Status | Notes |
|-------------|--------|-------|
| `RequestHeaderModifier` | ❌ Not Implemented | Add/Set/Remove request headers not supported |
| `ResponseHeaderModifier` | ❌ Not Implemented | Add/Set/Remove response headers not supported |
| `RequestRedirect` | ❌ Not Implemented | HTTP redirects not supported |
| `URLRewrite` | ❌ Not Implemented | Path/hostname rewriting not supported |
| `RequestMirror` | ❌ Not Implemented | Traffic mirroring not supported |
| `ExtensionRef` | ❌ Not Implemented | Custom filters not supported |

### spec.rules[].backendRefs

| Field | Status | Notes |
|-------|--------|-------|
| `backendRefs[].name` | ✅ Supported | Service name |
| `backendRefs[].namespace` | ⚠️ Partial | Not explicitly handled, likely defaults to route namespace |
| `backendRefs[].port` | ✅ Supported | Service port number |
| `backendRefs[].weight` | ✅ Supported | Traffic splitting with weighted distribution |
| `backendRefs[].filters[]` | ❌ Not Implemented | Per-backend filters not supported |
| Multiple backends | ✅ Supported | Weighted traffic splitting using MULTIBACKEND qualifier |
| Single backend | ✅ Supported | Optimized with BACKEND qualifier (avoids weighted logic) |
| Omitted weight | ✅ Supported | Defaults to weight 1 |

**Weighted Backend Implementation:**

The gateway library uses HAProxy's `rand()` function and map-based selection for O(1) weighted routing:
- Weights are pre-expanded into map entries (e.g., 70/30 split = 100 map entries)
- Entry 0-69 map to backend 1, entries 70-99 map to backend 2
- HAProxy generates random number % total_weight and looks up backend in map

**Example - Weighted traffic splitting:**

```yaml
spec:
  rules:
    - matches:
        - path:
            type: PathPrefix
            value: /app
      backendRefs:
        # 70% of traffic
        - name: app-v1
          port: 80
          weight: 70
        # 30% of traffic
        - name: app-v2
          port: 80
          weight: 30
```

**Example - Default weights:**

```yaml
spec:
  rules:
    - backendRefs:
        # Omitted weight defaults to 1 (50/50 split)
        - name: backend-a
          port: 80
        - name: backend-b
          port: 80
```

### Advanced Features

**Backend Deduplication:**

The template automatically deduplicates backends when multiple routes reference the same service+port combination, preventing duplicate HAProxy backend definitions.

**Route Key Generation:**

Internal route identifiers use the format `namespace_routename_ruleindex` to ensure uniqueness across namespaces and rules.

## GRPCRoute Support

### spec.parentRefs

| Field | Status | Notes |
|-------|--------|-------|
| All fields | ⚠️ Similar to HTTPRoute | Same template pattern and limitations |

### spec.hostnames

| Field | Status | Notes |
|-------|--------|-------|
| `hostnames[]` | ✅ Supported | Multiple hostnames per route |

### spec.rules[].matches

| Field | Status | Notes |
|-------|--------|-------|
| `matches[].method.type: Exact` | ❌ Not Implemented | Method matching fields exist but no routing logic |
| `matches[].method.type: RegularExpression` | ❌ Not Implemented | Regex method matching not implemented |
| `matches[].method.service` | ❌ Not Implemented | gRPC service name not used for routing |
| `matches[].method.method` | ❌ Not Implemented | gRPC method name not used for routing |
| `matches[].headers[]` | ❌ Not Implemented | Header matching not implemented |

**Important:** Validation tests reference `method` fields but no template logic implements method-based routing. Backends are generated with HTTP/2 protocol support, but all gRPC requests to a hostname route to the same backend regardless of service/method.

### spec.rules[].filters

| Filter Type | Status | Notes |
|-------------|--------|-------|
| `RequestHeaderModifier` | ❌ Not Implemented | |
| `ResponseHeaderModifier` | ❌ Not Implemented | |
| `RequestMirror` | ❌ Not Implemented | |
| `ExtensionRef` | ❌ Not Implemented | |

### spec.rules[].backendRefs

| Field | Status | Notes |
|-------|--------|-------|
| All `backendRefs` fields | ✅ Supported | Same implementation as HTTPRoute |
| HTTP/2 protocol | ✅ Supported | Backends generated with `proto h2` flag |

**Example - GRPCRoute:**

```yaml
apiVersion: gateway.networking.k8s.io/v1
kind: GRPCRoute
metadata:
  name: grpc-example
spec:
  hostnames:
    - "grpc.example.com"
  rules:
    - backendRefs:
        - name: grpc-svc
          port: 9090
```

## Known Limitations

### Critical Gaps

1. **GRPCRoute method routing not implemented** - While backends are generated with HTTP/2 support, the `matches[].method` fields are not used for routing decisions. All gRPC traffic to a hostname goes to the same backend.

2. **No filter support** - All filter types (header modification, redirects, rewrites, mirroring) are not implemented for either HTTPRoute or GRPCRoute.

3. **No header/query parameter matching** - HTTPRoute cannot route based on HTTP headers or query parameters, only path matching is supported.

### Untested Features

- Cross-namespace backend references
- Cross-namespace parent Gateway references
- Wildcard hostname patterns
- Listener-specific route attachment (`sectionName`)

## Testing Coverage

The gateway library includes comprehensive validation tests:

**Well-tested:**
- HTTPRoute path matching (Exact, PathPrefix, RegularExpression)
- HTTPRoute weighted backends (various weight combinations, defaults)
- HTTPRoute default behaviors (no matches → PathPrefix /)
- Backend deduplication (multiple routes to same service+port)
- GRPCRoute backend generation with HTTP/2

**Untested:**
- GRPCRoute method-based routing (no tests verify method matching)
- Cross-namespace references
- Wildcard hostnames
- Any filter types
- Header or query parameter matching

## Future Development

Priority areas for future enhancement:

1. **GRPCRoute method routing** - Implement routing based on `matches[].method.service` and `matches[].method.method`
2. **Request header matching** - Support HTTPRoute and GRPCRoute header-based routing
3. **Basic filters** - Start with `RequestHeaderModifier` and `ResponseHeaderModifier`
4. **Query parameter matching** - Add HTTPRoute query param support
5. **Cross-namespace testing** - Validate cross-namespace references work correctly

## See Also

- [Gateway API Documentation](https://gateway-api.sigs.k8s.io/)
- [HAProxy Configuration Reference](../../docs/supported-configuration.md)
- [Template Library Architecture](../CLAUDE.md)
