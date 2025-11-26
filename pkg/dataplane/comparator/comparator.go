package comparator

import (
	"fmt"

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

// compareMapEntries is a generic helper for comparing map-based child entries (nameservers, mailer entries, peer entries).
// This reduces code duplication for the common pattern of comparing map[string]T entries.
func compareMapEntries[T any](
	currentMap, desiredMap map[string]T,
	createOp func(*T) Operation,
	deleteOp func(*T) Operation,
	updateOp func(*T) Operation,
	equalFunc func(*T, *T) bool,
) []Operation {
	var operations []Operation

	// Handle nil maps
	if currentMap == nil {
		currentMap = make(map[string]T)
	}
	if desiredMap == nil {
		desiredMap = make(map[string]T)
	}

	// Find added entries
	for name := range desiredMap {
		if _, exists := currentMap[name]; !exists {
			entry := desiredMap[name]
			operations = append(operations, createOp(&entry))
		}
	}

	// Find deleted entries
	for name := range currentMap {
		if _, exists := desiredMap[name]; !exists {
			entry := currentMap[name]
			operations = append(operations, deleteOp(&entry))
		}
	}

	// Find modified entries
	for name := range desiredMap {
		currentEntry, exists := currentMap[name]
		if !exists {
			continue
		}
		desiredEntry := desiredMap[name]

		// Compare entry attributes
		if !equalFunc(&currentEntry, &desiredEntry) {
			operations = append(operations, updateOp(&desiredEntry))
		}
	}

	return operations
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
	//       operations = append(operations, sections.NewFrontendUpdate(frontend2))
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
