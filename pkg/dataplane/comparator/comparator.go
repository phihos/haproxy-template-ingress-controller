package comparator

import (
	"encoding/json"
	"fmt"

	"github.com/haproxytech/client-native/v6/models"

	"haproxy-template-ic/codegen/dataplaneapi"
	"haproxy-template-ic/pkg/dataplane/comparator/sections"
	"haproxy-template-ic/pkg/dataplane/parser"
)

const (
	parentTypeFrontend = "frontend"
	parentTypeBackend  = "backend"
)

// Comparator performs fine-grained comparison between HAProxy configurations.
//
// It generates the minimal set of operations needed to transform a current
// configuration into a desired configuration, using attribute-level granularity
// to minimize API calls and avoid unnecessary HAProxy reloads.
type Comparator struct {
	// Future: Add section-specific comparators here
	// backendComparator *sections.BackendComparator
	// serverComparator  *sections.ServerComparator
}

// New creates a new Comparator instance.
func New() *Comparator {
	return &Comparator{}
}

// appendOperationsIfNotEmpty is a helper method that appends operations and marks as modified if operations exist.
// This reduces cyclomatic complexity by extracting the common pattern used throughout comparison functions.
func appendOperationsIfNotEmpty(dst *[]Operation, src []Operation, modified *bool) {
	if len(src) > 0 {
		*dst = append(*dst, src...)
		*modified = true
	}
}

// Compare performs a deep comparison between current and desired configurations.
//
// It returns a ConfigDiff containing all operations needed to transform
// current into desired, along with a summary of changes.
//
// The comparison is performed at attribute-level granularity - if only a
// single attribute changes (e.g., server weight), only that attribute is
// updated rather than replacing the entire resource.
//
// Example:
//
//	comparator := comparator.New()
//	diff, err := comparator.Compare(currentConfig, desiredConfig)
//	if err != nil {
//	    log.Fatal(err)
//	}
//
//	fmt.Printf("Changes: %s\n", diff.Summary.String())
//	for _, op := range diff.Operations {
//	    fmt.Printf("- %s\n", op.Describe())
//	}
func (c *Comparator) Compare(current, desired *parser.StructuredConfig) (*ConfigDiff, error) {
	if current == nil {
		return nil, fmt.Errorf("current configuration is nil")
	}
	if desired == nil {
		return nil, fmt.Errorf("desired configuration is nil")
	}

	summary := NewDiffSummary()
	var operations []Operation

	// Compare global section
	globalOps := c.compareGlobal(current, desired, &summary)
	operations = append(operations, globalOps...)

	// Compare defaults sections
	defaultsOps := c.compareDefaults(current, desired, &summary)
	operations = append(operations, defaultsOps...)

	// Compare http-errors sections
	httpErrorsOps := c.compareHTTPErrors(current, desired)
	operations = append(operations, httpErrorsOps...)

	// Compare resolvers
	resolversOps := c.compareResolvers(current, desired)
	operations = append(operations, resolversOps...)

	// Compare mailers
	mailersOps := c.compareMailers(current, desired)
	operations = append(operations, mailersOps...)

	// Compare peers
	peersOps := c.comparePeers(current, desired)
	operations = append(operations, peersOps...)

	// Compare caches
	cachesOps := c.compareCaches(current, desired)
	operations = append(operations, cachesOps...)

	// Compare rings
	ringsOps := c.compareRings(current, desired)
	operations = append(operations, ringsOps...)

	// Compare userlists
	userlistsOps := c.compareUserlists(current, desired)
	operations = append(operations, userlistsOps...)

	// Compare programs
	programsOps := c.comparePrograms(current, desired)
	operations = append(operations, programsOps...)

	// Compare log-forwards
	logForwardsOps := c.compareLogForwards(current, desired)
	operations = append(operations, logForwardsOps...)

	// Compare fcgi-apps
	fcgiAppsOps := c.compareFCGIApps(current, desired)
	operations = append(operations, fcgiAppsOps...)

	// Compare crt-stores
	crtStoresOps := c.compareCrtStores(current, desired)
	operations = append(operations, crtStoresOps...)

	// Compare frontends
	frontendOps := c.compareFrontends(current, desired, &summary)
	operations = append(operations, frontendOps...)

	// Compare backends
	backendOps := c.compareBackends(current, desired, &summary)
	operations = append(operations, backendOps...)

	// Future: Add more section comparisons here using the .Equal() pattern:
	//
	// PATTERN: Always use models' built-in .Equal() methods instead of manual field comparison.
	// This approach:
	//   - Automatically handles ALL attributes (current + future)
	//   - Zero maintenance burden when HAProxy adds new parameters
	//   - Since we sync entire directives/lines anyway, there's no benefit to field-level comparison
	//
	// Example for Frontends:
	//   if !frontend1.Equal(*frontend2) {
	//       operations = append(operations, sections.NewUpdateFrontendOperation(frontend2))
	//   }
	//
	// Sections to implement:
	// - Global settings (models.Global.Equal)
	// - Defaults (models.Defaults.Equal)
	// - Frontends (models.Frontend.Equal)
	// - ACLs (models.ACL.Equal)
	// - Rules (models.Rule.Equal)
	// etc.

	// Update summary counts
	for _, op := range operations {
		switch op.Type() {
		case sections.OperationCreate:
			summary.TotalCreates++
		case sections.OperationUpdate:
			summary.TotalUpdates++
		case sections.OperationDelete:
			summary.TotalDeletes++
		}
	}

	// Order operations by dependencies
	orderedOps := OrderOperations(operations)

	return &ConfigDiff{
		Operations: orderedOps,
		Summary:    summary,
	}, nil
}

// compareBackends compares backend configurations between current and desired.
//
// This is a focused implementation that handles the most common use case:
// backend and server management. It demonstrates the pattern for other sections.
//
//nolint:dupl // Similar pattern to compareFrontends but handles different type (Backend vs Frontend)
func (c *Comparator) compareBackends(current, desired *parser.StructuredConfig, summary *DiffSummary) []Operation {
	var operations []Operation

	// Build maps for easier comparison
	currentBackends := make(map[string]*models.Backend)
	for _, backend := range current.Backends {
		if backend.Name != "" {
			currentBackends[backend.Name] = backend
		}
	}

	desiredBackends := make(map[string]*models.Backend)
	for _, backend := range desired.Backends {
		if backend.Name != "" {
			desiredBackends[backend.Name] = backend
		}
	}

	// Find added backends
	addedOps := c.compareAddedBackends(desiredBackends, currentBackends, summary)
	operations = append(operations, addedOps...)

	// Find deleted backends
	for name, backend := range currentBackends {
		if _, exists := desiredBackends[name]; !exists {
			operations = append(operations, sections.NewDeleteBackendOperation(backend))
			summary.BackendsDeleted = append(summary.BackendsDeleted, name)
		}
	}

	// Find modified backends
	modifiedOps := c.compareModifiedBackends(desiredBackends, currentBackends, summary)
	operations = append(operations, modifiedOps...)

	return operations
}

// compareAddedBackends compares added backends and creates operations for them and their nested elements.
func (c *Comparator) compareAddedBackends(desiredBackends, currentBackends map[string]*models.Backend, summary *DiffSummary) []Operation {
	// Pre-allocate with estimated capacity (at least one operation per backend)
	operations := make([]Operation, 0, len(desiredBackends))

	for name, backend := range desiredBackends {
		if _, exists := currentBackends[name]; exists {
			continue
		}
		operations = append(operations, sections.NewCreateBackendOperation(backend))
		summary.BackendsAdded = append(summary.BackendsAdded, name)

		// Also create servers for this new backend
		// Compare against an empty backend to get all server create operations
		emptyBackend := &models.Backend{}
		emptyBackend.Name = name
		emptyBackend.Servers = make(map[string]models.Server)
		serverOps := c.compareServers(name, emptyBackend, backend, summary)
		if len(serverOps) > 0 {
			operations = append(operations, serverOps...)
		}

		// Also create server templates for this new backend
		emptyBackend.ServerTemplates = make(map[string]models.ServerTemplate)
		serverTemplateOps := c.compareServerTemplates(name, emptyBackend, backend)
		if len(serverTemplateOps) > 0 {
			operations = append(operations, serverTemplateOps...)
		}
	}

	return operations
}

// compareModifiedBackends compares modified backends and creates operations for changed nested elements.
func (c *Comparator) compareModifiedBackends(desiredBackends, currentBackends map[string]*models.Backend, summary *DiffSummary) []Operation {
	var operations []Operation

	for name, desiredBackend := range desiredBackends {
		currentBackend, exists := currentBackends[name]
		if !exists {
			continue
		}
		backendModified := false

		// Compare servers within this backend
		serverOps := c.compareServers(name, currentBackend, desiredBackend, summary)
		appendOperationsIfNotEmpty(&operations, serverOps, &backendModified)

		// Compare ACLs within this backend
		aclOps := c.compareACLs("backend", name, currentBackend.ACLList, desiredBackend.ACLList, summary)
		appendOperationsIfNotEmpty(&operations, aclOps, &backendModified)

		// Compare HTTP request rules within this backend
		requestRuleOps := c.compareHTTPRequestRules("backend", name, currentBackend.HTTPRequestRuleList, desiredBackend.HTTPRequestRuleList)
		appendOperationsIfNotEmpty(&operations, requestRuleOps, &backendModified)

		// Compare HTTP response rules within this backend
		responseRuleOps := c.compareHTTPResponseRules("backend", name, currentBackend.HTTPResponseRuleList, desiredBackend.HTTPResponseRuleList)
		appendOperationsIfNotEmpty(&operations, responseRuleOps, &backendModified)

		// Compare TCP request rules within this backend
		tcpRequestRuleOps := c.compareTCPRequestRules("backend", name, currentBackend.TCPRequestRuleList, desiredBackend.TCPRequestRuleList)
		appendOperationsIfNotEmpty(&operations, tcpRequestRuleOps, &backendModified)

		// Compare TCP response rules within this backend
		tcpResponseRuleOps := c.compareTCPResponseRules(name, currentBackend.TCPResponseRuleList, desiredBackend.TCPResponseRuleList)
		appendOperationsIfNotEmpty(&operations, tcpResponseRuleOps, &backendModified)

		// Compare log targets within this backend
		logTargetOps := c.compareLogTargets("backend", name, currentBackend.LogTargetList, desiredBackend.LogTargetList)
		appendOperationsIfNotEmpty(&operations, logTargetOps, &backendModified)

		// Compare stick rules within this backend
		stickRuleOps := c.compareStickRules(name, currentBackend.StickRuleList, desiredBackend.StickRuleList)
		appendOperationsIfNotEmpty(&operations, stickRuleOps, &backendModified)

		// Compare HTTP after response rules within this backend
		httpAfterRuleOps := c.compareHTTPAfterResponseRules(name, currentBackend.HTTPAfterResponseRuleList, desiredBackend.HTTPAfterResponseRuleList)
		appendOperationsIfNotEmpty(&operations, httpAfterRuleOps, &backendModified)

		// Compare server switching rules within this backend
		serverSwitchingRuleOps := c.compareServerSwitchingRules(name, currentBackend.ServerSwitchingRuleList, desiredBackend.ServerSwitchingRuleList)
		appendOperationsIfNotEmpty(&operations, serverSwitchingRuleOps, &backendModified)

		// Compare filters within this backend
		filterOps := c.compareFilters("backend", name, currentBackend.FilterList, desiredBackend.FilterList)
		appendOperationsIfNotEmpty(&operations, filterOps, &backendModified)

		// Compare HTTP checks within this backend
		httpCheckOps := c.compareHTTPChecks(name, currentBackend.HTTPCheckList, desiredBackend.HTTPCheckList)
		appendOperationsIfNotEmpty(&operations, httpCheckOps, &backendModified)

		// Compare TCP checks within this backend
		tcpCheckOps := c.compareTCPChecks(name, currentBackend.TCPCheckRuleList, desiredBackend.TCPCheckRuleList)
		appendOperationsIfNotEmpty(&operations, tcpCheckOps, &backendModified)

		// Compare server templates within this backend
		serverTemplateOps := c.compareServerTemplates(name, currentBackend, desiredBackend)
		appendOperationsIfNotEmpty(&operations, serverTemplateOps, &backendModified)

		// Compare backend attributes (excluding servers, ACLs, and rules which we already compared)
		if !backendsEqualWithoutNestedCollections(currentBackend, desiredBackend) {
			operations = append(operations, sections.NewUpdateBackendOperation(desiredBackend))
			backendModified = true
		}

		if backendModified {
			summary.BackendsModified = append(summary.BackendsModified, name)
		}
	}

	return operations
}

// compareServers compares server configurations within a backend.
func (c *Comparator) compareServers(backendName string, currentBackend, desiredBackend *models.Backend, summary *DiffSummary) []Operation {
	var operations []Operation

	// Backend.Servers is already a map[string]models.Server
	currentServers := currentBackend.Servers
	desiredServers := desiredBackend.Servers

	// Find added servers
	addedOps := c.compareAddedServers(backendName, currentServers, desiredServers, summary)
	operations = append(operations, addedOps...)

	// Find deleted servers
	deletedOps := c.compareDeletedServers(backendName, currentServers, desiredServers, summary)
	operations = append(operations, deletedOps...)

	// Find modified servers
	modifiedOps := c.compareModifiedServers(backendName, currentServers, desiredServers, summary)
	operations = append(operations, modifiedOps...)

	return operations
}

// compareAddedServers compares added servers and creates operations for them.
func (c *Comparator) compareAddedServers(backendName string, currentServers, desiredServers map[string]models.Server, summary *DiffSummary) []Operation {
	var operations []Operation

	for name := range desiredServers {
		if _, exists := currentServers[name]; !exists {
			server := desiredServers[name]
			operations = append(operations, sections.NewCreateServerOperation(backendName, &server))
			if summary.ServersAdded[backendName] == nil {
				summary.ServersAdded[backendName] = []string{}
			}
			summary.ServersAdded[backendName] = append(summary.ServersAdded[backendName], name)
		}
	}

	return operations
}

// compareDeletedServers compares deleted servers and creates operations for them.
func (c *Comparator) compareDeletedServers(backendName string, currentServers, desiredServers map[string]models.Server, summary *DiffSummary) []Operation {
	var operations []Operation

	for name := range currentServers {
		if _, exists := desiredServers[name]; !exists {
			server := currentServers[name]
			operations = append(operations, sections.NewDeleteServerOperation(backendName, &server))
			if summary.ServersDeleted[backendName] == nil {
				summary.ServersDeleted[backendName] = []string{}
			}
			summary.ServersDeleted[backendName] = append(summary.ServersDeleted[backendName], name)
		}
	}

	return operations
}

// compareModifiedServers compares modified servers and creates operations for them.
func (c *Comparator) compareModifiedServers(backendName string, currentServers, desiredServers map[string]models.Server, summary *DiffSummary) []Operation {
	var operations []Operation

	for name := range desiredServers {
		currentServer, exists := currentServers[name]
		if !exists {
			continue
		}
		desiredServer := desiredServers[name]

		// Compare server attributes
		// For now, we check if anything changed - future implementation
		// will do fine-grained attribute comparison
		if !serversEqual(&currentServer, &desiredServer) {
			operations = append(operations, sections.NewUpdateServerOperation(backendName, &desiredServer))
			if summary.ServersModified[backendName] == nil {
				summary.ServersModified[backendName] = []string{}
			}
			summary.ServersModified[backendName] = append(summary.ServersModified[backendName], name)
		}
	}

	return operations
}

// serversEqual checks if two servers are equal.
// Uses the HAProxy models' built-in Equal() method to compare ALL attributes.
// This approach automatically handles current and future server parameters without
// maintenance burden, since we sync the entire server line anyway.
func serversEqual(s1, s2 *models.Server) bool {
	return s1.Equal(*s2)
}

// frontendsEqualWithoutNestedCollections checks if two frontends are equal, excluding ACLs, HTTP rules, and binds.
// Uses the HAProxy models' built-in Equal() method to compare ALL frontend attributes
// (mode, timeouts, etc.) automatically, excluding nested collections we compare separately.
func frontendsEqualWithoutNestedCollections(f1, f2 *models.Frontend) bool {
	// Create copies to avoid modifying originals
	f1Copy := *f1
	f2Copy := *f2

	// Clear nested collections so they don't affect comparison
	f1Copy.ACLList = nil
	f2Copy.ACLList = nil
	f1Copy.HTTPRequestRuleList = nil
	f2Copy.HTTPRequestRuleList = nil
	f1Copy.HTTPResponseRuleList = nil
	f2Copy.HTTPResponseRuleList = nil
	f1Copy.TCPRequestRuleList = nil
	f2Copy.TCPRequestRuleList = nil
	f1Copy.BackendSwitchingRuleList = nil
	f2Copy.BackendSwitchingRuleList = nil
	f1Copy.LogTargetList = nil
	f2Copy.LogTargetList = nil
	f1Copy.Binds = nil
	f2Copy.Binds = nil
	f1Copy.FilterList = nil
	f2Copy.FilterList = nil
	f1Copy.CaptureList = nil
	f2Copy.CaptureList = nil

	return f1Copy.Equal(f2Copy)
}

// backendsEqualWithoutNestedCollections checks if two backends are equal, excluding servers, ACLs, and HTTP rules.
// Uses the HAProxy models' built-in Equal() method to compare ALL backend attributes
// (mode, balance algorithm, timeouts, health checks, etc.) automatically, excluding nested collections we compare separately.
func backendsEqualWithoutNestedCollections(b1, b2 *models.Backend) bool {
	// Create copies to avoid modifying originals
	b1Copy := *b1
	b2Copy := *b2

	// Clear nested collections so they don't affect comparison
	b1Copy.Servers = nil
	b2Copy.Servers = nil
	b1Copy.ACLList = nil
	b2Copy.ACLList = nil
	b1Copy.HTTPRequestRuleList = nil
	b2Copy.HTTPRequestRuleList = nil
	b1Copy.HTTPResponseRuleList = nil
	b2Copy.HTTPResponseRuleList = nil
	b1Copy.HTTPAfterResponseRuleList = nil
	b2Copy.HTTPAfterResponseRuleList = nil
	b1Copy.TCPRequestRuleList = nil
	b2Copy.TCPRequestRuleList = nil
	b1Copy.TCPResponseRuleList = nil
	b2Copy.TCPResponseRuleList = nil
	b1Copy.ServerSwitchingRuleList = nil
	b2Copy.ServerSwitchingRuleList = nil
	b1Copy.LogTargetList = nil
	b2Copy.LogTargetList = nil
	b1Copy.StickRuleList = nil
	b2Copy.StickRuleList = nil
	b1Copy.FilterList = nil
	b2Copy.FilterList = nil
	b1Copy.HTTPCheckList = nil
	b2Copy.HTTPCheckList = nil
	b1Copy.TCPCheckRuleList = nil
	b2Copy.TCPCheckRuleList = nil
	b1Copy.ServerTemplates = nil
	b2Copy.ServerTemplates = nil

	return b1Copy.Equal(b2Copy)
}

// compareFrontends compares frontend configurations between current and desired.
//
//nolint:dupl // Similar pattern to compareBackends but handles different type (Frontend vs Backend)
func (c *Comparator) compareFrontends(current, desired *parser.StructuredConfig, summary *DiffSummary) []Operation {
	var operations []Operation

	// Build maps for easier comparison
	currentFrontends := make(map[string]*models.Frontend)
	for _, frontend := range current.Frontends {
		if frontend.Name != "" {
			currentFrontends[frontend.Name] = frontend
		}
	}

	desiredFrontends := make(map[string]*models.Frontend)
	for _, frontend := range desired.Frontends {
		if frontend.Name != "" {
			desiredFrontends[frontend.Name] = frontend
		}
	}

	// Find added frontends
	addedOps := c.compareAddedFrontends(desiredFrontends, currentFrontends, summary)
	operations = append(operations, addedOps...)

	// Find deleted frontends
	for name, frontend := range currentFrontends {
		if _, exists := desiredFrontends[name]; !exists {
			operations = append(operations, sections.NewDeleteFrontendOperation(frontend))
			summary.FrontendsDeleted = append(summary.FrontendsDeleted, name)
		}
	}

	// Find modified frontends
	modifiedOps := c.compareModifiedFrontends(desiredFrontends, currentFrontends, summary)
	operations = append(operations, modifiedOps...)

	return operations
}

// compareAddedFrontends compares added frontends and creates operations for them and their nested elements.
func (c *Comparator) compareAddedFrontends(desiredFrontends, currentFrontends map[string]*models.Frontend, summary *DiffSummary) []Operation {
	// Pre-allocate with estimated capacity (at least one operation per frontend)
	operations := make([]Operation, 0, len(desiredFrontends))

	for name, frontend := range desiredFrontends {
		if _, exists := currentFrontends[name]; exists {
			continue
		}
		operations = append(operations, sections.NewCreateFrontendOperation(frontend))
		summary.FrontendsAdded = append(summary.FrontendsAdded, name)

		// Also create operations for nested elements in this new frontend
		// Compare against an empty frontend to get all nested element create operations
		emptyFrontend := &models.Frontend{}
		emptyFrontend.Name = name

		// Compare ACLs
		aclOps := c.compareACLs(parentTypeFrontend, name, emptyFrontend.ACLList, frontend.ACLList, summary)
		operations = append(operations, aclOps...)

		// Compare HTTP request rules
		requestRuleOps := c.compareHTTPRequestRules(parentTypeFrontend, name, emptyFrontend.HTTPRequestRuleList, frontend.HTTPRequestRuleList)
		operations = append(operations, requestRuleOps...)

		// Compare HTTP response rules
		responseRuleOps := c.compareHTTPResponseRules(parentTypeFrontend, name, emptyFrontend.HTTPResponseRuleList, frontend.HTTPResponseRuleList)
		operations = append(operations, responseRuleOps...)

		// Compare TCP request rules
		tcpRequestRuleOps := c.compareTCPRequestRules(parentTypeFrontend, name, emptyFrontend.TCPRequestRuleList, frontend.TCPRequestRuleList)
		operations = append(operations, tcpRequestRuleOps...)

		// Compare backend switching rules
		backendSwitchingRuleOps := c.compareBackendSwitchingRules(name, emptyFrontend.BackendSwitchingRuleList, frontend.BackendSwitchingRuleList)
		operations = append(operations, backendSwitchingRuleOps...)

		// Compare filters
		filterOps := c.compareFilters(parentTypeFrontend, name, emptyFrontend.FilterList, frontend.FilterList)
		operations = append(operations, filterOps...)

		// Compare captures
		captureOps := c.compareCaptures(name, emptyFrontend.CaptureList, frontend.CaptureList)
		operations = append(operations, captureOps...)

		// Compare log targets
		logTargetOps := c.compareLogTargets(parentTypeFrontend, name, emptyFrontend.LogTargetList, frontend.LogTargetList)
		operations = append(operations, logTargetOps...)

		// Compare binds
		emptyBinds := make(map[string]models.Bind)
		bindOps := c.compareBinds(name, emptyBinds, frontend.Binds)
		operations = append(operations, bindOps...)
	}

	return operations
}

// compareModifiedFrontends compares modified frontends and creates operations for changed nested elements.
func (c *Comparator) compareModifiedFrontends(desiredFrontends, currentFrontends map[string]*models.Frontend, summary *DiffSummary) []Operation {
	var operations []Operation

	for name, desiredFrontend := range desiredFrontends {
		currentFrontend, exists := currentFrontends[name]
		if !exists {
			continue
		}
		frontendModified := false

		// Compare ACLs within this frontend
		aclOps := c.compareACLs(parentTypeFrontend, name, currentFrontend.ACLList, desiredFrontend.ACLList, summary)
		appendOperationsIfNotEmpty(&operations, aclOps, &frontendModified)

		// Compare HTTP request rules within this frontend
		requestRuleOps := c.compareHTTPRequestRules(parentTypeFrontend, name, currentFrontend.HTTPRequestRuleList, desiredFrontend.HTTPRequestRuleList)
		appendOperationsIfNotEmpty(&operations, requestRuleOps, &frontendModified)

		// Compare HTTP response rules within this frontend
		responseRuleOps := c.compareHTTPResponseRules(parentTypeFrontend, name, currentFrontend.HTTPResponseRuleList, desiredFrontend.HTTPResponseRuleList)
		appendOperationsIfNotEmpty(&operations, responseRuleOps, &frontendModified)

		// Compare TCP request rules within this frontend
		tcpRequestRuleOps := c.compareTCPRequestRules(parentTypeFrontend, name, currentFrontend.TCPRequestRuleList, desiredFrontend.TCPRequestRuleList)
		appendOperationsIfNotEmpty(&operations, tcpRequestRuleOps, &frontendModified)

		// Compare backend switching rules within this frontend
		backendSwitchingRuleOps := c.compareBackendSwitchingRules(name, currentFrontend.BackendSwitchingRuleList, desiredFrontend.BackendSwitchingRuleList)
		appendOperationsIfNotEmpty(&operations, backendSwitchingRuleOps, &frontendModified)

		// Compare filters within this frontend
		filterOps := c.compareFilters(parentTypeFrontend, name, currentFrontend.FilterList, desiredFrontend.FilterList)
		appendOperationsIfNotEmpty(&operations, filterOps, &frontendModified)

		// Compare captures within this frontend
		captureOps := c.compareCaptures(name, currentFrontend.CaptureList, desiredFrontend.CaptureList)
		appendOperationsIfNotEmpty(&operations, captureOps, &frontendModified)

		// Compare log targets within this frontend
		logTargetOps := c.compareLogTargets(parentTypeFrontend, name, currentFrontend.LogTargetList, desiredFrontend.LogTargetList)
		appendOperationsIfNotEmpty(&operations, logTargetOps, &frontendModified)

		// Compare binds within this frontend
		bindOps := c.compareBinds(name, currentFrontend.Binds, desiredFrontend.Binds)
		appendOperationsIfNotEmpty(&operations, bindOps, &frontendModified)

		// Compare frontend attributes (excluding ACLs, rules, and binds which we already compared)
		// Create copies to compare without nested collections
		if !frontendsEqualWithoutNestedCollections(currentFrontend, desiredFrontend) {
			operations = append(operations, sections.NewUpdateFrontendOperation(desiredFrontend))
			frontendModified = true
		}

		if frontendModified {
			summary.FrontendsModified = append(summary.FrontendsModified, name)
		}
	}

	return operations
}

// compareGlobal compares global section configurations between current and desired.
// The global section is a singleton - it always exists and can only be updated, not created or deleted.
func (c *Comparator) compareGlobal(current, desired *parser.StructuredConfig, summary *DiffSummary) []Operation {
	var operations []Operation

	// Both configs should have a global section (even if empty)
	// If either is nil, we skip comparison
	if current.Global == nil || desired.Global == nil {
		return operations
	}

	// Compare using built-in Equal() method
	// This automatically compares all global attributes (log settings, stats socket, maxconn, etc.)
	if !current.Global.Equal(*desired.Global) {
		operations = append(operations, sections.NewUpdateGlobalOperation(desired.Global))
		summary.GlobalChanged = true
	}

	return operations
}

// compareDefaults compares defaults section configurations between current and desired.
// HAProxy can have multiple defaults sections (identified by name).
func (c *Comparator) compareDefaults(current, desired *parser.StructuredConfig, summary *DiffSummary) []Operation {
	var operations []Operation

	// Build maps for easier comparison
	currentDefaults := make(map[string]*models.Defaults)
	for _, defaults := range current.Defaults {
		if defaults.Name != "" {
			currentDefaults[defaults.Name] = defaults
		}
	}

	desiredDefaults := make(map[string]*models.Defaults)
	for _, defaults := range desired.Defaults {
		if defaults.Name != "" {
			desiredDefaults[defaults.Name] = defaults
		}
	}

	// Find added defaults sections
	for name, defaults := range desiredDefaults {
		if _, exists := currentDefaults[name]; !exists {
			operations = append(operations, sections.NewCreateDefaultsOperation(defaults))
			summary.DefaultsChanged = true
		}
	}

	// Find deleted defaults sections
	for name, defaults := range currentDefaults {
		if _, exists := desiredDefaults[name]; !exists {
			operations = append(operations, sections.NewDeleteDefaultsOperation(defaults))
			summary.DefaultsChanged = true
		}
	}

	// Find modified defaults sections
	for name, desiredDefaults := range desiredDefaults {
		if currentDefaults, exists := currentDefaults[name]; exists {
			// Compare using built-in Equal() method
			// This automatically compares all defaults attributes (mode, timeouts, options, etc.)
			if !currentDefaults.Equal(*desiredDefaults) {
				operations = append(operations, sections.NewUpdateDefaultsOperation(desiredDefaults))
				summary.DefaultsChanged = true
			}
		}
	}

	return operations
}

// compareACLs compares ACL configurations within a frontend or backend.
// ACLs are identified by their name (ACLName field).
//
//nolint:unparam // summary parameter kept for consistency with other compare functions
func (c *Comparator) compareACLs(parentType, parentName string, currentACLs, desiredACLs models.Acls, summary *DiffSummary) []Operation {
	var operations []Operation

	// Build maps for easier comparison using ACL names
	currentACLMap := make(map[string]int) // name -> index
	for i, acl := range currentACLs {
		if acl.ACLName != "" {
			currentACLMap[acl.ACLName] = i
		}
	}

	desiredACLMap := make(map[string]int) // name -> index
	for i, acl := range desiredACLs {
		if acl.ACLName != "" {
			desiredACLMap[acl.ACLName] = i
		}
	}

	// Find added ACLs
	addedOps := c.compareAddedACLs(parentType, parentName, desiredACLMap, currentACLMap, desiredACLs)
	operations = append(operations, addedOps...)

	// Find deleted ACLs
	deletedOps := c.compareDeletedACLs(parentType, parentName, currentACLMap, desiredACLMap, currentACLs)
	operations = append(operations, deletedOps...)

	// Find modified ACLs
	modifiedOps := c.compareModifiedACLs(parentType, parentName, desiredACLMap, currentACLMap, currentACLs, desiredACLs)
	operations = append(operations, modifiedOps...)

	return operations
}

// compareAddedACLs compares added ACLs and creates operations for them.
func (c *Comparator) compareAddedACLs(parentType, parentName string, desiredACLMap, currentACLMap map[string]int, desiredACLs models.Acls) []Operation {
	var operations []Operation

	for name, idx := range desiredACLMap {
		if _, exists := currentACLMap[name]; !exists {
			acl := desiredACLs[idx]
			if parentType == parentTypeFrontend {
				operations = append(operations, sections.NewCreateACLFrontendOperation(parentName, acl, idx))
			} else {
				operations = append(operations, sections.NewCreateACLBackendOperation(parentName, acl, idx))
			}
		}
	}

	return operations
}

// compareDeletedACLs compares deleted ACLs and creates operations for them.
func (c *Comparator) compareDeletedACLs(parentType, parentName string, currentACLMap, desiredACLMap map[string]int, currentACLs models.Acls) []Operation {
	var operations []Operation

	for name, idx := range currentACLMap {
		if _, exists := desiredACLMap[name]; !exists {
			acl := currentACLs[idx]
			if parentType == parentTypeFrontend {
				operations = append(operations, sections.NewDeleteACLFrontendOperation(parentName, acl, idx))
			} else {
				operations = append(operations, sections.NewDeleteACLBackendOperation(parentName, acl, idx))
			}
		}
	}

	return operations
}

// compareModifiedACLs compares modified ACLs and creates operations for them.
func (c *Comparator) compareModifiedACLs(parentType, parentName string, desiredACLMap, currentACLMap map[string]int, currentACLs, desiredACLs models.Acls) []Operation {
	var operations []Operation

	for name, desiredIdx := range desiredACLMap {
		if currentIdx, exists := currentACLMap[name]; exists {
			currentACL := currentACLs[currentIdx]
			desiredACL := desiredACLs[desiredIdx]

			// Compare using built-in Equal() method
			if !currentACL.Equal(*desiredACL) {
				if parentType == parentTypeFrontend {
					operations = append(operations, sections.NewUpdateACLFrontendOperation(parentName, desiredACL, desiredIdx))
				} else {
					operations = append(operations, sections.NewUpdateACLBackendOperation(parentName, desiredACL, desiredIdx))
				}
			}
		}
	}

	return operations
}

// compareHTTPRequestRules compares HTTP request rule configurations within a frontend or backend.
// Rules are compared by position since they don't have unique identifiers.
func (c *Comparator) compareHTTPRequestRules(parentType, parentName string, currentRules, desiredRules models.HTTPRequestRules) []Operation {
	var operations []Operation

	// Compare rules by position
	maxLen := len(currentRules)
	if len(desiredRules) > maxLen {
		maxLen = len(desiredRules)
	}

	for i := 0; i < maxLen; i++ {
		hasCurrentRule := i < len(currentRules)
		hasDesiredRule := i < len(desiredRules)

		if !hasCurrentRule && hasDesiredRule {
			ops := c.createHTTPRequestRuleOperation(parentType, parentName, desiredRules[i], i)
			operations = append(operations, ops...)
		} else if hasCurrentRule && !hasDesiredRule {
			ops := c.deleteHTTPRequestRuleOperation(parentType, parentName, currentRules[i], i)
			operations = append(operations, ops...)
		} else if hasCurrentRule && hasDesiredRule {
			ops := c.updateHTTPRequestRuleOperation(parentType, parentName, currentRules[i], desiredRules[i], i)
			operations = append(operations, ops...)
		}
	}

	return operations
}

func (c *Comparator) createHTTPRequestRuleOperation(parentType, parentName string, rule *models.HTTPRequestRule, index int) []Operation {
	if parentType == parentTypeFrontend {
		return []Operation{sections.NewCreateHTTPRequestRuleFrontendOperation(parentName, rule, index)}
	}
	return []Operation{sections.NewCreateHTTPRequestRuleBackendOperation(parentName, rule, index)}
}

func (c *Comparator) deleteHTTPRequestRuleOperation(parentType, parentName string, rule *models.HTTPRequestRule, index int) []Operation {
	if parentType == parentTypeFrontend {
		return []Operation{sections.NewDeleteHTTPRequestRuleFrontendOperation(parentName, rule, index)}
	}
	return []Operation{sections.NewDeleteHTTPRequestRuleBackendOperation(parentName, rule, index)}
}

func (c *Comparator) updateHTTPRequestRuleOperation(parentType, parentName string, currentRule, desiredRule *models.HTTPRequestRule, index int) []Operation {
	if !currentRule.Equal(*desiredRule) {
		if parentType == parentTypeFrontend {
			return []Operation{sections.NewUpdateHTTPRequestRuleFrontendOperation(parentName, desiredRule, index)}
		}
		return []Operation{sections.NewUpdateHTTPRequestRuleBackendOperation(parentName, desiredRule, index)}
	}
	return nil
}

// compareHTTPResponseRules compares HTTP response rule configurations within a frontend or backend.
// Rules are compared by position since they don't have unique identifiers.
func (c *Comparator) compareHTTPResponseRules(parentType, parentName string, currentRules, desiredRules models.HTTPResponseRules) []Operation {
	var operations []Operation

	// Compare rules by position
	maxLen := len(currentRules)
	if len(desiredRules) > maxLen {
		maxLen = len(desiredRules)
	}

	for i := 0; i < maxLen; i++ {
		hasCurrentRule := i < len(currentRules)
		hasDesiredRule := i < len(desiredRules)

		if !hasCurrentRule && hasDesiredRule {
			ops := c.createHTTPResponseRuleOperation(parentType, parentName, desiredRules[i], i)
			operations = append(operations, ops...)
		} else if hasCurrentRule && !hasDesiredRule {
			ops := c.deleteHTTPResponseRuleOperation(parentType, parentName, currentRules[i], i)
			operations = append(operations, ops...)
		} else if hasCurrentRule && hasDesiredRule {
			ops := c.updateHTTPResponseRuleOperation(parentType, parentName, currentRules[i], desiredRules[i], i)
			operations = append(operations, ops...)
		}
	}

	return operations
}

func (c *Comparator) createHTTPResponseRuleOperation(parentType, parentName string, rule *models.HTTPResponseRule, index int) []Operation {
	if parentType == parentTypeFrontend {
		return []Operation{sections.NewCreateHTTPResponseRuleFrontendOperation(parentName, rule, index)}
	}
	return []Operation{sections.NewCreateHTTPResponseRuleBackendOperation(parentName, rule, index)}
}

func (c *Comparator) deleteHTTPResponseRuleOperation(parentType, parentName string, rule *models.HTTPResponseRule, index int) []Operation {
	if parentType == parentTypeFrontend {
		return []Operation{sections.NewDeleteHTTPResponseRuleFrontendOperation(parentName, rule, index)}
	}
	return []Operation{sections.NewDeleteHTTPResponseRuleBackendOperation(parentName, rule, index)}
}

func (c *Comparator) updateHTTPResponseRuleOperation(parentType, parentName string, currentRule, desiredRule *models.HTTPResponseRule, index int) []Operation {
	if !currentRule.Equal(*desiredRule) {
		if parentType == parentTypeFrontend {
			return []Operation{sections.NewUpdateHTTPResponseRuleFrontendOperation(parentName, desiredRule, index)}
		}
		return []Operation{sections.NewUpdateHTTPResponseRuleBackendOperation(parentName, desiredRule, index)}
	}
	return nil
}

// compareTCPRequestRules compares TCP request rule configurations within a frontend or backend.
// Rules are compared by position since they don't have unique identifiers.
func (c *Comparator) compareTCPRequestRules(parentType, parentName string, currentRules, desiredRules models.TCPRequestRules) []Operation {
	var operations []Operation

	// Compare rules by position
	maxLen := len(currentRules)
	if len(desiredRules) > maxLen {
		maxLen = len(desiredRules)
	}

	for i := 0; i < maxLen; i++ {
		hasCurrentRule := i < len(currentRules)
		hasDesiredRule := i < len(desiredRules)

		if !hasCurrentRule && hasDesiredRule {
			ops := c.createTCPRequestRuleOperation(parentType, parentName, desiredRules[i], i)
			operations = append(operations, ops...)
		} else if hasCurrentRule && !hasDesiredRule {
			ops := c.deleteTCPRequestRuleOperation(parentType, parentName, currentRules[i], i)
			operations = append(operations, ops...)
		} else if hasCurrentRule && hasDesiredRule {
			ops := c.updateTCPRequestRuleOperation(parentType, parentName, currentRules[i], desiredRules[i], i)
			operations = append(operations, ops...)
		}
	}

	return operations
}

func (c *Comparator) createTCPRequestRuleOperation(parentType, parentName string, rule *models.TCPRequestRule, index int) []Operation {
	if parentType == parentTypeFrontend {
		return []Operation{sections.NewCreateTCPRequestRuleFrontendOperation(parentName, rule, index)}
	}
	return []Operation{sections.NewCreateTCPRequestRuleBackendOperation(parentName, rule, index)}
}

func (c *Comparator) deleteTCPRequestRuleOperation(parentType, parentName string, rule *models.TCPRequestRule, index int) []Operation {
	if parentType == parentTypeFrontend {
		return []Operation{sections.NewDeleteTCPRequestRuleFrontendOperation(parentName, rule, index)}
	}
	return []Operation{sections.NewDeleteTCPRequestRuleBackendOperation(parentName, rule, index)}
}

func (c *Comparator) updateTCPRequestRuleOperation(parentType, parentName string, currentRule, desiredRule *models.TCPRequestRule, index int) []Operation {
	if !currentRule.Equal(*desiredRule) {
		if parentType == parentTypeFrontend {
			return []Operation{sections.NewUpdateTCPRequestRuleFrontendOperation(parentName, desiredRule, index)}
		}
		return []Operation{sections.NewUpdateTCPRequestRuleBackendOperation(parentName, desiredRule, index)}
	}
	return nil
}

// compareTCPResponseRules compares TCP response rule configurations within a backend.
// Rules are compared by position since they don't have unique identifiers.
//
//nolint:dupl // Similar pattern to other backend-only rule comparison functions (StickRules, HTTPAfterResponseRules, etc.) - each handles different rule types
func (c *Comparator) compareTCPResponseRules(parentName string, currentRules, desiredRules models.TCPResponseRules) []Operation {
	var operations []Operation

	// Compare rules by position
	maxLen := len(currentRules)
	if len(desiredRules) > maxLen {
		maxLen = len(desiredRules)
	}

	for i := 0; i < maxLen; i++ {
		hasCurrentRule := i < len(currentRules)
		hasDesiredRule := i < len(desiredRules)

		if !hasCurrentRule && hasDesiredRule {
			// Rule added at this position
			rule := desiredRules[i]
			operations = append(operations, sections.NewCreateTCPResponseRuleBackendOperation(parentName, rule, i))
		} else if hasCurrentRule && !hasDesiredRule {
			// Rule removed at this position
			rule := currentRules[i]
			operations = append(operations, sections.NewDeleteTCPResponseRuleBackendOperation(parentName, rule, i))
		} else if hasCurrentRule && hasDesiredRule {
			// Both exist - check if modified
			currentRule := currentRules[i]
			desiredRule := desiredRules[i]

			if !currentRule.Equal(*desiredRule) {
				operations = append(operations, sections.NewUpdateTCPResponseRuleBackendOperation(parentName, desiredRule, i))
			}
		}
	}

	return operations
}

// compareLogTargets compares log target configurations within a frontend or backend.
// Log targets are compared by position since they don't have unique identifiers.
func (c *Comparator) compareLogTargets(parentType, parentName string, currentLogs, desiredLogs models.LogTargets) []Operation {
	var operations []Operation

	// Compare log targets by position
	maxLen := len(currentLogs)
	if len(desiredLogs) > maxLen {
		maxLen = len(desiredLogs)
	}

	for i := 0; i < maxLen; i++ {
		hasCurrentLog := i < len(currentLogs)
		hasDesiredLog := i < len(desiredLogs)

		if !hasCurrentLog && hasDesiredLog {
			ops := c.createLogTargetOperation(parentType, parentName, desiredLogs[i], i)
			operations = append(operations, ops...)
		} else if hasCurrentLog && !hasDesiredLog {
			ops := c.deleteLogTargetOperation(parentType, parentName, currentLogs[i], i)
			operations = append(operations, ops...)
		} else if hasCurrentLog && hasDesiredLog {
			ops := c.updateLogTargetOperation(parentType, parentName, currentLogs[i], desiredLogs[i], i)
			operations = append(operations, ops...)
		}
	}

	return operations
}

func (c *Comparator) createLogTargetOperation(parentType, parentName string, logTarget *models.LogTarget, index int) []Operation {
	if parentType == parentTypeFrontend {
		return []Operation{sections.NewCreateLogTargetFrontendOperation(parentName, logTarget, index)}
	}
	return []Operation{sections.NewCreateLogTargetBackendOperation(parentName, logTarget, index)}
}

func (c *Comparator) deleteLogTargetOperation(parentType, parentName string, logTarget *models.LogTarget, index int) []Operation {
	if parentType == parentTypeFrontend {
		return []Operation{sections.NewDeleteLogTargetFrontendOperation(parentName, logTarget, index)}
	}
	return []Operation{sections.NewDeleteLogTargetBackendOperation(parentName, logTarget, index)}
}

func (c *Comparator) updateLogTargetOperation(parentType, parentName string, currentLog, desiredLog *models.LogTarget, index int) []Operation {
	if !currentLog.Equal(*desiredLog) {
		if parentType == parentTypeFrontend {
			return []Operation{sections.NewUpdateLogTargetFrontendOperation(parentName, desiredLog, index)}
		}
		return []Operation{sections.NewUpdateLogTargetBackendOperation(parentName, desiredLog, index)}
	}
	return nil
}

// compareStickRules compares stick rule configurations within a backend.

// Stick rules are compared by position since they don't have unique identifiers.
// Backend-only (frontends do not support stick rules).
//
//nolint:dupl // Similar pattern to other backend-only rule comparison functions - each handles different rule types
func (c *Comparator) compareStickRules(backendName string, currentRules, desiredRules models.StickRules) []Operation {
	var operations []Operation

	// Compare stick rules by position
	maxLen := len(currentRules)
	if len(desiredRules) > maxLen {
		maxLen = len(desiredRules)
	}

	for i := 0; i < maxLen; i++ {
		hasCurrentRule := i < len(currentRules)
		hasDesiredRule := i < len(desiredRules)

		if !hasCurrentRule && hasDesiredRule {
			// Stick rule added at this position
			rule := desiredRules[i]
			operations = append(operations, sections.NewCreateStickRuleBackendOperation(backendName, rule, i))
		} else if hasCurrentRule && !hasDesiredRule {
			// Stick rule removed at this position
			rule := currentRules[i]
			operations = append(operations, sections.NewDeleteStickRuleBackendOperation(backendName, rule, i))
		} else if hasCurrentRule && hasDesiredRule {
			// Both exist - check if modified
			currentRule := currentRules[i]
			desiredRule := desiredRules[i]

			if !currentRule.Equal(*desiredRule) {
				operations = append(operations, sections.NewUpdateStickRuleBackendOperation(backendName, desiredRule, i))
			}
		}
	}

	return operations
}

// compareHTTPAfterResponseRules compares HTTP after response rule configurations within a backend.

// Rules are compared by position since they don't have unique identifiers.
// Backend-only (frontends do not support HTTP after response rules).
//
//nolint:dupl // Similar pattern to other backend-only rule comparison functions - each handles different rule types
func (c *Comparator) compareHTTPAfterResponseRules(backendName string, currentRules, desiredRules models.HTTPAfterResponseRules) []Operation {
	var operations []Operation

	// Compare rules by position
	maxLen := len(currentRules)
	if len(desiredRules) > maxLen {
		maxLen = len(desiredRules)
	}

	for i := 0; i < maxLen; i++ {
		hasCurrentRule := i < len(currentRules)
		hasDesiredRule := i < len(desiredRules)

		if !hasCurrentRule && hasDesiredRule {
			// Rule added at this position
			rule := desiredRules[i]
			operations = append(operations, sections.NewCreateHTTPAfterResponseRuleBackendOperation(backendName, rule, i))
		} else if hasCurrentRule && !hasDesiredRule {
			// Rule removed at this position
			rule := currentRules[i]
			operations = append(operations, sections.NewDeleteHTTPAfterResponseRuleBackendOperation(backendName, rule, i))
		} else if hasCurrentRule && hasDesiredRule {
			// Both exist - check if modified
			currentRule := currentRules[i]
			desiredRule := desiredRules[i]

			if !currentRule.Equal(*desiredRule) {
				operations = append(operations, sections.NewUpdateHTTPAfterResponseRuleBackendOperation(backendName, desiredRule, i))
			}
		}
	}

	return operations
}

// compareBackendSwitchingRules compares backend switching rule configurations within a frontend.
// Rules are compared by position since they don't have unique identifiers.
//
//nolint:dupl // Similar pattern to other switching/check rule comparison functions - each handles different types
func (c *Comparator) compareBackendSwitchingRules(frontendName string, currentRules, desiredRules models.BackendSwitchingRules) []Operation {
	var operations []Operation

	// Compare rules by position
	maxLen := len(currentRules)
	if len(desiredRules) > maxLen {
		maxLen = len(desiredRules)
	}

	for i := 0; i < maxLen; i++ {
		hasCurrentRule := i < len(currentRules)
		hasDesiredRule := i < len(desiredRules)

		if !hasCurrentRule && hasDesiredRule {
			// Rule added at this position
			rule := desiredRules[i]
			operations = append(operations, sections.NewCreateBackendSwitchingRuleFrontendOperation(frontendName, rule, i))
		} else if hasCurrentRule && !hasDesiredRule {
			// Rule removed at this position
			rule := currentRules[i]
			operations = append(operations, sections.NewDeleteBackendSwitchingRuleFrontendOperation(frontendName, rule, i))
		} else if hasCurrentRule && hasDesiredRule {
			// Both exist - check if modified
			currentRule := currentRules[i]
			desiredRule := desiredRules[i]

			if !currentRule.Equal(*desiredRule) {
				operations = append(operations, sections.NewUpdateBackendSwitchingRuleFrontendOperation(frontendName, desiredRule, i))
			}
		}
	}

	return operations
}

// compareServerSwitchingRules compares server switching rule configurations within a backend.
// Rules are compared by position since they don't have unique identifiers.
//
//nolint:dupl // Similar pattern to other switching/check rule comparison functions - each handles different types
func (c *Comparator) compareServerSwitchingRules(backendName string, currentRules, desiredRules models.ServerSwitchingRules) []Operation {
	var operations []Operation

	// Compare rules by position
	maxLen := len(currentRules)
	if len(desiredRules) > maxLen {
		maxLen = len(desiredRules)
	}

	for i := 0; i < maxLen; i++ {
		hasCurrentRule := i < len(currentRules)
		hasDesiredRule := i < len(desiredRules)

		if !hasCurrentRule && hasDesiredRule {
			// Rule added at this position
			rule := desiredRules[i]
			operations = append(operations, sections.NewCreateServerSwitchingRuleBackendOperation(backendName, rule, i))
		} else if hasCurrentRule && !hasDesiredRule {
			// Rule removed at this position
			rule := currentRules[i]
			operations = append(operations, sections.NewDeleteServerSwitchingRuleBackendOperation(backendName, rule, i))
		} else if hasCurrentRule && hasDesiredRule {
			// Both exist - check if modified
			currentRule := currentRules[i]
			desiredRule := desiredRules[i]

			if !currentRule.Equal(*desiredRule) {
				operations = append(operations, sections.NewUpdateServerSwitchingRuleBackendOperation(backendName, desiredRule, i))
			}
		}
	}

	return operations
}

// compareBinds compares bind configurations within a frontend.
// Binds are identified by their name (Name field in the map key).
func (c *Comparator) compareBinds(frontendName string, currentBinds, desiredBinds map[string]models.Bind) []Operation {
	var operations []Operation

	// Find added binds
	for name := range desiredBinds {
		if _, exists := currentBinds[name]; !exists {
			bind := desiredBinds[name]
			// Convert models.Bind to dataplaneapi.Bind
			apiBind := convertToAPIBind(&bind)
			operations = append(operations, sections.NewCreateBindFrontendOperation(frontendName, name, apiBind))
		}
	}

	// Find deleted binds
	for name := range currentBinds {
		if _, exists := desiredBinds[name]; !exists {
			bind := currentBinds[name]
			// Convert models.Bind to dataplaneapi.Bind
			apiBind := convertToAPIBind(&bind)
			operations = append(operations, sections.NewDeleteBindFrontendOperation(frontendName, name, apiBind))
		}
	}

	// Find modified binds
	for name := range desiredBinds {
		currentBind, exists := currentBinds[name]
		if !exists {
			continue
		}
		desiredBind := desiredBinds[name]
		// Compare using built-in Equal() method
		if !currentBind.Equal(desiredBind) {
			// Convert models.Bind to dataplaneapi.Bind
			apiBind := convertToAPIBind(&desiredBind)
			operations = append(operations, sections.NewUpdateBindFrontendOperation(frontendName, name, apiBind))
		}
	}

	return operations
}

// convertToAPIBind converts a models.Bind to dataplaneapi.Bind using JSON marshaling.
func convertToAPIBind(modelBind *models.Bind) *dataplaneapi.Bind {
	if modelBind == nil {
		return nil
	}

	data, err := json.Marshal(modelBind)
	if err != nil {
		// This should never happen with valid models.Bind
		return nil
	}

	var apiBind dataplaneapi.Bind
	if err := json.Unmarshal(data, &apiBind); err != nil {
		// This should never happen with valid JSON
		return nil
	}

	return &apiBind
}

// compareFilters compares filter configurations within a frontend or backend.
// Filters are compared by position since they don't have unique identifiers.
func (c *Comparator) compareFilters(parentType, parentName string, currentFilters, desiredFilters models.Filters) []Operation {
	var operations []Operation

	// Compare filters by position
	maxLen := len(currentFilters)
	if len(desiredFilters) > maxLen {
		maxLen = len(desiredFilters)
	}

	for i := 0; i < maxLen; i++ {
		hasCurrentFilter := i < len(currentFilters)
		hasDesiredFilter := i < len(desiredFilters)

		if !hasCurrentFilter && hasDesiredFilter {
			ops := c.createFilterOperation(parentType, parentName, desiredFilters[i], i)
			operations = append(operations, ops...)
		} else if hasCurrentFilter && !hasDesiredFilter {
			ops := c.deleteFilterOperation(parentType, parentName, currentFilters[i], i)
			operations = append(operations, ops...)
		} else if hasCurrentFilter && hasDesiredFilter {
			ops := c.updateFilterOperation(parentType, parentName, currentFilters[i], desiredFilters[i], i)
			operations = append(operations, ops...)
		}
	}

	return operations
}

func (c *Comparator) createFilterOperation(parentType, parentName string, filter *models.Filter, index int) []Operation {
	if parentType == parentTypeFrontend {
		return []Operation{sections.NewCreateFilterFrontendOperation(parentName, filter, index)}
	}
	return []Operation{sections.NewCreateFilterBackendOperation(parentName, filter, index)}
}

func (c *Comparator) deleteFilterOperation(parentType, parentName string, filter *models.Filter, index int) []Operation {
	if parentType == parentTypeFrontend {
		return []Operation{sections.NewDeleteFilterFrontendOperation(parentName, filter, index)}
	}
	return []Operation{sections.NewDeleteFilterBackendOperation(parentName, filter, index)}
}

func (c *Comparator) updateFilterOperation(parentType, parentName string, currentFilter, desiredFilter *models.Filter, index int) []Operation {
	if !currentFilter.Equal(*desiredFilter) {
		if parentType == parentTypeFrontend {
			return []Operation{sections.NewUpdateFilterFrontendOperation(parentName, desiredFilter, index)}
		}
		return []Operation{sections.NewUpdateFilterBackendOperation(parentName, desiredFilter, index)}
	}
	return nil
}

// compareHTTPChecks compares HTTP check configurations within a backend.
// HTTP checks are compared by position since they don't have unique identifiers.
//
//nolint:dupl // Similar pattern to compareTCPChecks - both handle check configurations with same logic but different types
func (c *Comparator) compareHTTPChecks(backendName string, currentChecks, desiredChecks models.HTTPChecks) []Operation {
	var operations []Operation

	// Compare checks by position
	maxLen := len(currentChecks)
	if len(desiredChecks) > maxLen {
		maxLen = len(desiredChecks)
	}

	for i := 0; i < maxLen; i++ {
		hasCurrentCheck := i < len(currentChecks)
		hasDesiredCheck := i < len(desiredChecks)

		if !hasCurrentCheck && hasDesiredCheck {
			// Check added at this position
			check := desiredChecks[i]
			operations = append(operations, sections.NewCreateHTTPCheckBackendOperation(backendName, check, i))
		} else if hasCurrentCheck && !hasDesiredCheck {
			// Check removed at this position
			check := currentChecks[i]
			operations = append(operations, sections.NewDeleteHTTPCheckBackendOperation(backendName, check, i))
		} else if hasCurrentCheck && hasDesiredCheck {
			// Both exist - check if modified
			currentCheck := currentChecks[i]
			desiredCheck := desiredChecks[i]

			if !currentCheck.Equal(*desiredCheck) {
				operations = append(operations, sections.NewUpdateHTTPCheckBackendOperation(backendName, desiredCheck, i))
			}
		}
	}

	return operations
}

// compareTCPChecks compares TCP check configurations within a backend.
// TCP checks are compared by position since they don't have unique identifiers.
//
//nolint:dupl // Similar pattern to compareHTTPChecks and compareCaptures - all handle positioned list comparisons with same logic but different types
func (c *Comparator) compareTCPChecks(backendName string, currentChecks, desiredChecks models.TCPChecks) []Operation {
	var operations []Operation

	// Compare checks by position
	maxLen := len(currentChecks)
	if len(desiredChecks) > maxLen {
		maxLen = len(desiredChecks)
	}

	for i := 0; i < maxLen; i++ {
		hasCurrentCheck := i < len(currentChecks)
		hasDesiredCheck := i < len(desiredChecks)

		if !hasCurrentCheck && hasDesiredCheck {
			// Check added at this position
			check := desiredChecks[i]
			operations = append(operations, sections.NewCreateTCPCheckBackendOperation(backendName, check, i))
		} else if hasCurrentCheck && !hasDesiredCheck {
			// Check removed at this position
			check := currentChecks[i]
			operations = append(operations, sections.NewDeleteTCPCheckBackendOperation(backendName, check, i))
		} else if hasCurrentCheck && hasDesiredCheck {
			// Both exist - check if modified
			currentCheck := currentChecks[i]
			desiredCheck := desiredChecks[i]

			if !currentCheck.Equal(*desiredCheck) {
				operations = append(operations, sections.NewUpdateTCPCheckBackendOperation(backendName, desiredCheck, i))
			}
		}
	}

	return operations
}

// compareCaptures compares capture configurations within a frontend.
// Captures are compared by position since they don't have unique identifiers.
//
//nolint:dupl // Similar pattern to HTTP/TCP checks and other positioned rule comparisons - each handles different types
func (c *Comparator) compareCaptures(frontendName string, currentCaptures, desiredCaptures models.Captures) []Operation {
	var operations []Operation

	// Compare captures by position
	maxLen := len(currentCaptures)
	if len(desiredCaptures) > maxLen {
		maxLen = len(desiredCaptures)
	}

	for i := 0; i < maxLen; i++ {
		hasCurrentCapture := i < len(currentCaptures)
		hasDesiredCapture := i < len(desiredCaptures)

		if !hasCurrentCapture && hasDesiredCapture {
			// Capture added at this position
			capture := desiredCaptures[i]
			operations = append(operations, sections.NewCreateCaptureFrontendOperation(frontendName, capture, i))
		} else if hasCurrentCapture && !hasDesiredCapture {
			// Capture removed at this position
			capture := currentCaptures[i]
			operations = append(operations, sections.NewDeleteCaptureFrontendOperation(frontendName, capture, i))
		} else if hasCurrentCapture && hasDesiredCapture {
			// Both exist - check if modified
			currentCapture := currentCaptures[i]
			desiredCapture := desiredCaptures[i]

			if !currentCapture.Equal(*desiredCapture) {
				operations = append(operations, sections.NewUpdateCaptureFrontendOperation(frontendName, desiredCapture, i))
			}
		}
	}

	return operations
}

// compareServerTemplates compares server template configurations within a backend.
func (c *Comparator) compareServerTemplates(backendName string, currentBackend, desiredBackend *models.Backend) []Operation {
	var operations []Operation

	// Backend.ServerTemplates is already a map[string]models.ServerTemplate
	currentTemplates := currentBackend.ServerTemplates
	desiredTemplates := desiredBackend.ServerTemplates

	// Find added server templates
	for prefix := range desiredTemplates {
		if _, exists := currentTemplates[prefix]; !exists {
			template := desiredTemplates[prefix]
			operations = append(operations, sections.NewCreateServerTemplateOperation(backendName, &template))
		}
	}

	// Find deleted server templates
	for prefix := range currentTemplates {
		if _, exists := desiredTemplates[prefix]; !exists {
			template := currentTemplates[prefix]
			operations = append(operations, sections.NewDeleteServerTemplateOperation(backendName, &template))
		}
	}

	// Find modified server templates
	for prefix := range desiredTemplates {
		currentTemplate, exists := currentTemplates[prefix]
		if !exists {
			continue
		}
		desiredTemplate := desiredTemplates[prefix]
		// Compare server template attributes using Equal() method
		if !serverTemplatesEqual(&currentTemplate, &desiredTemplate) {
			operations = append(operations, sections.NewUpdateServerTemplateOperation(backendName, &desiredTemplate))
		}
	}

	return operations
}

// serverTemplatesEqual checks if two server templates are equal.
// Uses the HAProxy models' built-in Equal() method to compare ALL attributes.
func serverTemplatesEqual(t1, t2 *models.ServerTemplate) bool {
	return t1.Equal(*t2)
}

// compareHTTPErrors compares http-errors sections between current and desired configurations.

//nolint:dupl // Similar pattern to other section comparison functions (Resolvers, Mailers, Peers, etc.) - each handles different types
func (c *Comparator) compareHTTPErrors(current, desired *parser.StructuredConfig) []Operation {
	var operations []Operation

	// Convert slices to maps for easier comparison by Name
	currentMap := make(map[string]*models.HTTPErrorsSection)
	for i := range current.HTTPErrors {
		httpError := current.HTTPErrors[i]
		if httpError.Name != "" {
			currentMap[httpError.Name] = httpError
		}
	}

	desiredMap := make(map[string]*models.HTTPErrorsSection)
	for i := range desired.HTTPErrors {
		httpError := desired.HTTPErrors[i]
		if httpError.Name != "" {
			desiredMap[httpError.Name] = httpError
		}
	}

	// Find added http-errors sections
	for name, httpError := range desiredMap {
		if _, exists := currentMap[name]; !exists {
			operations = append(operations, sections.NewCreateHTTPErrorsOperation(httpError))
		}
	}

	// Find deleted http-errors sections
	for name, httpError := range currentMap {
		if _, exists := desiredMap[name]; !exists {
			operations = append(operations, sections.NewDeleteHTTPErrorsOperation(httpError))
		}
	}

	// Find modified http-errors sections
	for name, desiredHTTPError := range desiredMap {
		if currentHTTPError, exists := currentMap[name]; exists {
			// Compare http-errors sections using Equal() method
			if !httpErrorsEqual(currentHTTPError, desiredHTTPError) {
				operations = append(operations, sections.NewUpdateHTTPErrorsOperation(desiredHTTPError))
			}
		}
	}

	return operations
}

// httpErrorsEqual compares two http-errors sections for equality.
func httpErrorsEqual(h1, h2 *models.HTTPErrorsSection) bool {
	return h1.Equal(*h2)
}

// compareResolvers compares resolver sections between current and desired configurations.

//nolint:dupl // Similar pattern to other section comparison functions (HTTPErrors, Mailers, Peers, etc.) - each handles different types
func (c *Comparator) compareResolvers(current, desired *parser.StructuredConfig) []Operation {
	var operations []Operation

	// Convert slices to maps for easier comparison by Name
	currentMap := make(map[string]*models.Resolver)
	for i := range current.Resolvers {
		resolver := current.Resolvers[i]
		if resolver.Name != "" {
			currentMap[resolver.Name] = resolver
		}
	}

	desiredMap := make(map[string]*models.Resolver)
	for i := range desired.Resolvers {
		resolver := desired.Resolvers[i]
		if resolver.Name != "" {
			desiredMap[resolver.Name] = resolver
		}
	}

	// Find added resolver sections
	for name, resolver := range desiredMap {
		if _, exists := currentMap[name]; !exists {
			operations = append(operations, sections.NewCreateResolverOperation(resolver))
		}
	}

	// Find deleted resolver sections
	for name, resolver := range currentMap {
		if _, exists := desiredMap[name]; !exists {
			operations = append(operations, sections.NewDeleteResolverOperation(resolver))
		}
	}

	// Find modified resolver sections
	for name, desiredResolver := range desiredMap {
		if currentResolver, exists := currentMap[name]; exists {
			if !resolverEqual(currentResolver, desiredResolver) {
				operations = append(operations, sections.NewUpdateResolverOperation(desiredResolver))
			}
		}
	}

	return operations
}

// resolverEqual compares two resolver sections for equality.
func resolverEqual(r1, r2 *models.Resolver) bool {
	return r1.Equal(*r2)
}

// compareMailers compares mailers sections between current and desired configurations.
func (c *Comparator) compareMailers(current, desired *parser.StructuredConfig) []Operation {
	operations := make([]Operation, 0, len(desired.Mailers))

	// Convert slices to maps for easier comparison by Name
	currentMap := make(map[string]*models.MailersSection)
	for i := range current.Mailers {
		mailers := current.Mailers[i]
		if mailers.Name != "" {
			currentMap[mailers.Name] = mailers
		}
	}

	desiredMap := make(map[string]*models.MailersSection)
	for i := range desired.Mailers {
		mailers := desired.Mailers[i]
		if mailers.Name != "" {
			desiredMap[mailers.Name] = mailers
		}
	}

	// Find added mailers sections
	for name, mailers := range desiredMap {
		if _, exists := currentMap[name]; exists {
			continue
		}

		operations = append(operations, sections.NewCreateMailersOperation(mailers))

		// Also create mailer entries for this new mailers section
		// Compare against an empty mailers section to get all mailer entry create operations
		emptyMailers := &models.MailersSection{}
		emptyMailers.Name = name
		emptyMailers.MailerEntries = make(map[string]models.MailerEntry)
		mailerEntryOps := c.compareMailerEntries(name, emptyMailers, mailers)
		if len(mailerEntryOps) > 0 {
			operations = append(operations, mailerEntryOps...)
		}
	}

	// Find deleted mailers sections
	for name, mailers := range currentMap {
		if _, exists := desiredMap[name]; !exists {
			operations = append(operations, sections.NewDeleteMailersOperation(mailers))
		}
	}

	// Find modified mailers sections
	for name, desiredMailers := range desiredMap {
		if currentMailers, exists := currentMap[name]; exists {
			mailersModified := false

			// Compare mailer entries within this mailers section
			mailerEntryOps := c.compareMailerEntries(name, currentMailers, desiredMailers)
			appendOperationsIfNotEmpty(&operations, mailerEntryOps, &mailersModified)

			// Compare mailers section attributes (excluding mailer entries which we already compared)
			if !mailersEqualWithoutMailerEntries(currentMailers, desiredMailers) {
				operations = append(operations, sections.NewUpdateMailersOperation(desiredMailers))
			}
		}
	}

	return operations
}

// mailersEqualWithoutMailerEntries checks if two mailers sections are equal, excluding mailer entries.
// Uses the HAProxy models' built-in Equal() method to compare mailers section attributes
// (name, timeout, etc.) automatically, excluding mailer entries we compare separately.
func mailersEqualWithoutMailerEntries(m1, m2 *models.MailersSection) bool {
	// Create copies to avoid modifying originals
	m1Copy := *m1
	m2Copy := *m2

	// Clear mailer entries so they don't affect comparison
	m1Copy.MailerEntries = nil
	m2Copy.MailerEntries = nil

	return m1Copy.Equal(m2Copy)
}

// compareMailerEntries compares mailer entry configurations within a mailers section.
func (c *Comparator) compareMailerEntries(mailersSection string, currentMailers, desiredMailers *models.MailersSection) []Operation {
	var operations []Operation

	// MailersSection.MailerEntries is already a map[string]models.MailerEntry
	currentEntries := currentMailers.MailerEntries
	if currentEntries == nil {
		currentEntries = make(map[string]models.MailerEntry)
	}

	desiredEntries := desiredMailers.MailerEntries
	if desiredEntries == nil {
		desiredEntries = make(map[string]models.MailerEntry)
	}

	// Find added mailer entries
	for name := range desiredEntries {
		if _, exists := currentEntries[name]; !exists {
			entry := desiredEntries[name]
			operations = append(operations, sections.NewCreateMailerEntryOperation(mailersSection, &entry))
		}
	}

	// Find deleted mailer entries
	for name := range currentEntries {
		if _, exists := desiredEntries[name]; !exists {
			entry := currentEntries[name]
			operations = append(operations, sections.NewDeleteMailerEntryOperation(mailersSection, &entry))
		}
	}

	// Find modified mailer entries
	for name := range desiredEntries {
		currentEntry, exists := currentEntries[name]
		if !exists {
			continue
		}
		desiredEntry := desiredEntries[name]

		// Compare mailer entry attributes
		if !mailerEntriesEqual(&currentEntry, &desiredEntry) {
			operations = append(operations, sections.NewUpdateMailerEntryOperation(mailersSection, &desiredEntry))
		}
	}

	return operations
}

// mailerEntriesEqual checks if two mailer entries are equal.
// Uses the HAProxy models' built-in Equal() method to compare ALL attributes.
func mailerEntriesEqual(e1, e2 *models.MailerEntry) bool {
	return e1.Equal(*e2)
}

// comparePeers compares peer sections between current and desired configurations.

//nolint:dupl // Similar pattern to other section comparison functions (HTTPErrors, Resolvers, Mailers, etc.) - each handles different types
func (c *Comparator) comparePeers(current, desired *parser.StructuredConfig) []Operation {
	var operations []Operation

	// Convert slices to maps for easier comparison by Name
	currentMap := make(map[string]*models.PeerSection)
	for i := range current.Peers {
		peer := current.Peers[i]
		if peer.Name != "" {
			currentMap[peer.Name] = peer
		}
	}

	desiredMap := make(map[string]*models.PeerSection)
	for i := range desired.Peers {
		peer := desired.Peers[i]
		if peer.Name != "" {
			desiredMap[peer.Name] = peer
		}
	}

	// Find added peer sections
	for name, peer := range desiredMap {
		if _, exists := currentMap[name]; !exists {
			operations = append(operations, sections.NewCreatePeerOperation(peer))
		}
	}

	// Find deleted peer sections
	for name, peer := range currentMap {
		if _, exists := desiredMap[name]; !exists {
			operations = append(operations, sections.NewDeletePeerOperation(peer))
		}
	}

	// Find modified peer sections
	// Note: HAProxy Dataplane API does not support updating peer sections
	// So we only detect added and deleted peer sections
	for name, desiredPeer := range desiredMap {
		if currentPeer, exists := currentMap[name]; exists {
			if !peerEqual(currentPeer, desiredPeer) {
				operations = append(operations, sections.NewUpdatePeerOperation(desiredPeer))
			}
		}
	}

	return operations
}

// peerEqual compares two peer sections for equality.
func peerEqual(p1, p2 *models.PeerSection) bool {
	return p1.Equal(*p2)
}

// compareCaches compares cache sections between current and desired configurations.
func (c *Comparator) compareCaches(current, desired *parser.StructuredConfig) []Operation {
	var operations []Operation

	// Convert slices to maps for easier comparison by Name
	currentMap := make(map[string]*models.Cache)
	for i := range current.Caches {
		cache := current.Caches[i]
		if cache.Name != nil && *cache.Name != "" {
			currentMap[*cache.Name] = cache
		}
	}

	desiredMap := make(map[string]*models.Cache)
	for i := range desired.Caches {
		cache := desired.Caches[i]
		if cache.Name != nil && *cache.Name != "" {
			desiredMap[*cache.Name] = cache
		}
	}

	// Find added cache sections
	for name, cache := range desiredMap {
		if _, exists := currentMap[name]; !exists {
			operations = append(operations, sections.NewCreateCacheOperation(cache))
		}
	}

	// Find deleted cache sections
	for name, cache := range currentMap {
		if _, exists := desiredMap[name]; !exists {
			operations = append(operations, sections.NewDeleteCacheOperation(cache))
		}
	}

	// Find modified cache sections
	for name, desiredCache := range desiredMap {
		if currentCache, exists := currentMap[name]; exists {
			if !cacheEqual(currentCache, desiredCache) {
				operations = append(operations, sections.NewUpdateCacheOperation(desiredCache))
			}
		}
	}

	return operations
}

// cacheEqual compares two cache sections for equality.
func cacheEqual(c1, c2 *models.Cache) bool {
	return c1.Equal(*c2)
}

// compareRings compares ring sections between current and desired configurations.

//nolint:dupl // Similar pattern to other section comparison functions (HTTPErrors, Resolvers, Mailers, etc.) - each handles different types
func (c *Comparator) compareRings(current, desired *parser.StructuredConfig) []Operation {
	var operations []Operation

	// Convert slices to maps for easier comparison by Name
	currentMap := make(map[string]*models.Ring)
	for i := range current.Rings {
		ring := current.Rings[i]
		if ring.Name != "" {
			currentMap[ring.Name] = ring
		}
	}

	desiredMap := make(map[string]*models.Ring)
	for i := range desired.Rings {
		ring := desired.Rings[i]
		if ring.Name != "" {
			desiredMap[ring.Name] = ring
		}
	}

	// Find added ring sections
	for name, ring := range desiredMap {
		if _, exists := currentMap[name]; !exists {
			operations = append(operations, sections.NewCreateRingOperation(ring))
		}
	}

	// Find deleted ring sections
	for name, ring := range currentMap {
		if _, exists := desiredMap[name]; !exists {
			operations = append(operations, sections.NewDeleteRingOperation(ring))
		}
	}

	// Find modified ring sections
	for name, desiredRing := range desiredMap {
		if currentRing, exists := currentMap[name]; exists {
			if !ringEqual(currentRing, desiredRing) {
				operations = append(operations, sections.NewUpdateRingOperation(desiredRing))
			}
		}
	}

	return operations
}

// ringEqual compares two ring sections for equality.
func ringEqual(r1, r2 *models.Ring) bool {
	return r1.Equal(*r2)
}

// compareUserlists compares userlist sections between current and desired configurations.
func (c *Comparator) compareUserlists(current, desired *parser.StructuredConfig) []Operation {
	var operations []Operation

	// Convert slices to maps for easier comparison by Name
	currentMap := make(map[string]*models.Userlist)
	for i := range current.Userlists {
		userlist := current.Userlists[i]
		if userlist.Name != "" {
			currentMap[userlist.Name] = userlist
		}
	}

	desiredMap := make(map[string]*models.Userlist)
	for i := range desired.Userlists {
		userlist := desired.Userlists[i]
		if userlist.Name != "" {
			desiredMap[userlist.Name] = userlist
		}
	}

	// Find added userlist sections
	for name, userlist := range desiredMap {
		if _, exists := currentMap[name]; !exists {
			operations = append(operations, sections.NewCreateUserlistOperation(userlist))
		}
	}

	// Find deleted userlist sections
	for name, userlist := range currentMap {
		if _, exists := desiredMap[name]; !exists {
			operations = append(operations, sections.NewDeleteUserlistOperation(userlist))
		}
	}

	// Find modified userlist sections
	// Note: UserList API doesn't support updates, so we delete and recreate
	for name, desiredUserlist := range desiredMap {
		if currentUserlist, exists := currentMap[name]; exists {
			if !userlistEqual(currentUserlist, desiredUserlist) {
				operations = append(operations, sections.NewDeleteUserlistOperation(currentUserlist), sections.NewCreateUserlistOperation(desiredUserlist))
			}
		}
	}

	return operations
}

// userlistEqual compares two userlist sections for equality.
func userlistEqual(u1, u2 *models.Userlist) bool {
	return u1.Equal(*u2)
}

// comparePrograms compares program sections between current and desired configurations.

//nolint:dupl // Similar pattern to other section comparison functions (HTTPErrors, Resolvers, Mailers, etc.) - each handles different types
func (c *Comparator) comparePrograms(current, desired *parser.StructuredConfig) []Operation {
	var operations []Operation

	// Convert slices to maps for easier comparison by Name
	currentMap := make(map[string]*models.Program)
	for i := range current.Programs {
		program := current.Programs[i]
		if program.Name != "" {
			currentMap[program.Name] = program
		}
	}

	desiredMap := make(map[string]*models.Program)
	for i := range desired.Programs {
		program := desired.Programs[i]
		if program.Name != "" {
			desiredMap[program.Name] = program
		}
	}

	// Find added program sections
	for name, program := range desiredMap {
		if _, exists := currentMap[name]; !exists {
			operations = append(operations, sections.NewCreateProgramOperation(program))
		}
	}

	// Find deleted program sections
	for name, program := range currentMap {
		if _, exists := desiredMap[name]; !exists {
			operations = append(operations, sections.NewDeleteProgramOperation(program))
		}
	}

	// Find modified program sections
	for name, desiredProgram := range desiredMap {
		if currentProgram, exists := currentMap[name]; exists {
			if !programEqual(currentProgram, desiredProgram) {
				operations = append(operations, sections.NewUpdateProgramOperation(desiredProgram))
			}
		}
	}

	return operations
}

// programEqual compares two program sections for equality.
func programEqual(p1, p2 *models.Program) bool {
	return p1.Equal(*p2)
}

// compareLogForwards compares log-forward sections between current and desired configurations.

//nolint:dupl // Similar pattern to other section comparison functions (HTTPErrors, Resolvers, Mailers, etc.) - each handles different types
func (c *Comparator) compareLogForwards(current, desired *parser.StructuredConfig) []Operation {
	var operations []Operation

	// Convert slices to maps for easier comparison by Name
	currentMap := make(map[string]*models.LogForward)
	for i := range current.LogForwards {
		logForward := current.LogForwards[i]
		if logForward.Name != "" {
			currentMap[logForward.Name] = logForward
		}
	}

	desiredMap := make(map[string]*models.LogForward)
	for i := range desired.LogForwards {
		logForward := desired.LogForwards[i]
		if logForward.Name != "" {
			desiredMap[logForward.Name] = logForward
		}
	}

	// Find added log-forward sections
	for name, logForward := range desiredMap {
		if _, exists := currentMap[name]; !exists {
			operations = append(operations, sections.NewCreateLogForwardOperation(logForward))
		}
	}

	// Find deleted log-forward sections
	for name, logForward := range currentMap {
		if _, exists := desiredMap[name]; !exists {
			operations = append(operations, sections.NewDeleteLogForwardOperation(logForward))
		}
	}

	// Find modified log-forward sections
	for name, desiredLogForward := range desiredMap {
		if currentLogForward, exists := currentMap[name]; exists {
			if !logForwardEqual(currentLogForward, desiredLogForward) {
				operations = append(operations, sections.NewUpdateLogForwardOperation(desiredLogForward))
			}
		}
	}

	return operations
}

// logForwardEqual compares two log-forward sections for equality.
func logForwardEqual(l1, l2 *models.LogForward) bool {
	return l1.Equal(*l2)
}

// compareFCGIApps compares fcgi-app sections between current and desired configurations.

//nolint:dupl // Similar pattern to other section comparison functions (HTTPErrors, Resolvers, Mailers, etc.) - each handles different types
func (c *Comparator) compareFCGIApps(current, desired *parser.StructuredConfig) []Operation {
	var operations []Operation

	// Convert slices to maps for easier comparison by Name
	currentMap := make(map[string]*models.FCGIApp)
	for i := range current.FCGIApps {
		fcgiApp := current.FCGIApps[i]
		if fcgiApp.Name != "" {
			currentMap[fcgiApp.Name] = fcgiApp
		}
	}

	desiredMap := make(map[string]*models.FCGIApp)
	for i := range desired.FCGIApps {
		fcgiApp := desired.FCGIApps[i]
		if fcgiApp.Name != "" {
			desiredMap[fcgiApp.Name] = fcgiApp
		}
	}

	// Find added fcgi-app sections
	for name, fcgiApp := range desiredMap {
		if _, exists := currentMap[name]; !exists {
			operations = append(operations, sections.NewCreateFCGIAppOperation(fcgiApp))
		}
	}

	// Find deleted fcgi-app sections
	for name, fcgiApp := range currentMap {
		if _, exists := desiredMap[name]; !exists {
			operations = append(operations, sections.NewDeleteFCGIAppOperation(fcgiApp))
		}
	}

	// Find modified fcgi-app sections
	for name, desiredFCGIApp := range desiredMap {
		if currentFCGIApp, exists := currentMap[name]; exists {
			if !fcgiAppEqual(currentFCGIApp, desiredFCGIApp) {
				operations = append(operations, sections.NewUpdateFCGIAppOperation(desiredFCGIApp))
			}
		}
	}

	return operations
}

// fcgiAppEqual compares two fcgi-app sections for equality.
func fcgiAppEqual(f1, f2 *models.FCGIApp) bool {
	return f1.Equal(*f2)
}

// compareCrtStores compares crt-store sections between current and desired configurations.

//nolint:dupl // Similar pattern to other section comparison functions (HTTPErrors, Resolvers, Mailers, etc.) - each handles different types
func (c *Comparator) compareCrtStores(current, desired *parser.StructuredConfig) []Operation {
	var operations []Operation

	// Convert slices to maps for easier comparison by Name
	currentMap := make(map[string]*models.CrtStore)
	for i := range current.CrtStores {
		crtStore := current.CrtStores[i]
		if crtStore.Name != "" {
			currentMap[crtStore.Name] = crtStore
		}
	}

	desiredMap := make(map[string]*models.CrtStore)
	for i := range desired.CrtStores {
		crtStore := desired.CrtStores[i]
		if crtStore.Name != "" {
			desiredMap[crtStore.Name] = crtStore
		}
	}

	// Find added crt-store sections
	for name, crtStore := range desiredMap {
		if _, exists := currentMap[name]; !exists {
			operations = append(operations, sections.NewCreateCrtStoreOperation(crtStore))
		}
	}

	// Find deleted crt-store sections
	for name, crtStore := range currentMap {
		if _, exists := desiredMap[name]; !exists {
			operations = append(operations, sections.NewDeleteCrtStoreOperation(crtStore))
		}
	}

	// Find modified crt-store sections
	for name, desiredCrtStore := range desiredMap {
		if currentCrtStore, exists := currentMap[name]; exists {
			if !crtStoreEqual(currentCrtStore, desiredCrtStore) {
				operations = append(operations, sections.NewUpdateCrtStoreOperation(desiredCrtStore))
			}
		}
	}

	return operations
}

// crtStoreEqual compares two crt-store sections for equality.
func crtStoreEqual(c1, c2 *models.CrtStore) bool {
	return c1.Equal(*c2)
}
