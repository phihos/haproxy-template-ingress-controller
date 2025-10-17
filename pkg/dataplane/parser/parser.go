// Package parser provides HAProxy configuration parsing using client-native library.
//
// This package wraps the haproxytech/client-native parser to parse HAProxy
// configurations from strings (in-memory, no disk I/O) into structured representations
// suitable for comparison and API operations.
//
// Semantic validation (checking resource availability, directive compatibility, etc.)
// is NOT performed here - that is handled by the external haproxy binary in later stages.
package parser

import (
	"fmt"
	"log/slog"
	"strings"

	parser "github.com/haproxytech/client-native/v6/config-parser"
	"github.com/haproxytech/client-native/v6/configuration"
	"github.com/haproxytech/client-native/v6/models"
)

// Parser wraps client-native's config-parser for parsing HAProxy configurations.
type Parser struct {
	parser parser.Parser
}

// StructuredConfig holds all parsed configuration sections.
// This represents the complete HAProxy configuration in structured form
// suitable for comparison and API operations.
type StructuredConfig struct {
	Global      *models.Global
	Defaults    []*models.Defaults
	Frontends   []*models.Frontend
	Backends    []*models.Backend
	Peers       []*models.PeerSection
	Resolvers   []*models.Resolver
	Mailers     []*models.MailersSection
	Caches      []*models.Cache
	Rings       []*models.Ring
	HTTPErrors  []*models.HTTPErrorsSection
	Userlists   []*models.Userlist
	Programs    []*models.Program
	LogForwards []*models.LogForward
	FCGIApps    []*models.FCGIApp
	CrtStores   []*models.CrtStore
}

// New creates a new Parser instance.
//
// The parser uses client-native's config-parser which provides robust parsing
// of HAProxy configuration syntax without requiring file I/O.
func New() (*Parser, error) {
	p, err := parser.New()
	if err != nil {
		return nil, fmt.Errorf("failed to create parser: %w", err)
	}
	return &Parser{
		parser: p,
	}, nil
}

// ParseFromString parses an HAProxy configuration string into a structured representation.
//
// The configuration string should contain valid HAProxy configuration syntax.
// Returns a StructuredConfig containing all parsed sections (global, defaults,
// frontends, backends, etc.) suitable for comparison and synchronization.
//
// Syntax validation is performed as part of parsing - any syntax errors will be returned.
// Semantic validation (resource availability, directive compatibility) is performed
// by HAProxy via the Dataplane API during configuration application.
//
// Example:
//
//	config := `
//	global
//	    daemon
//	defaults
//	    mode http
//	backend web
//	    balance roundrobin
//	    server srv1 192.168.1.10:80
//	`
//	parser, _ := parser.New()
//	structured, err := parser.ParseFromString(config)
func (p *Parser) ParseFromString(config string) (*StructuredConfig, error) {
	if config == "" {
		return nil, fmt.Errorf("configuration string is empty")
	}

	// Parse directly from string - NO file I/O
	// This keeps all config data in memory as required
	// Syntax validation happens automatically during parsing
	if err := p.parser.Process(strings.NewReader(config)); err != nil {
		return nil, fmt.Errorf("failed to parse configuration: %w", err)
	}

	// Extract structured configuration from parser
	conf, err := p.extractConfiguration()
	if err != nil {
		return nil, fmt.Errorf("failed to extract configuration: %w", err)
	}

	return conf, nil
}

// extractConfiguration builds a StructuredConfig from the parsed data.
//
// This reads all sections (global, defaults, frontends, backends, etc.)
// from the client-native parser and assembles them into a complete
// configuration structure.
//
// Note: This extracts the parsed structure but does NOT validate semantics.
// The config-parser only ensures syntax correctness.
func (p *Parser) extractConfiguration() (*StructuredConfig, error) {
	conf := &StructuredConfig{}

	// Extract global section
	global, err := p.extractGlobal()
	if err != nil {
		return nil, fmt.Errorf("failed to extract global section: %w", err)
	}
	conf.Global = global

	// Extract defaults sections (HAProxy supports multiple defaults sections)
	defaults, err := p.extractDefaults()
	if err != nil {
		return nil, fmt.Errorf("failed to extract defaults sections: %w", err)
	}
	conf.Defaults = defaults

	// Extract frontends
	frontends, err := p.extractFrontends()
	if err != nil {
		return nil, fmt.Errorf("failed to extract frontends: %w", err)
	}
	conf.Frontends = frontends

	// Extract backends
	backends, err := p.extractBackends()
	if err != nil {
		return nil, fmt.Errorf("failed to extract backends: %w", err)
	}
	conf.Backends = backends

	// Extract peers
	peers, err := p.extractPeers()
	if err != nil {
		return nil, fmt.Errorf("failed to extract peers: %w", err)
	}
	conf.Peers = peers

	// Extract resolvers
	resolvers, err := p.extractResolvers()
	if err != nil {
		return nil, fmt.Errorf("failed to extract resolvers: %w", err)
	}
	conf.Resolvers = resolvers

	// Extract mailers
	mailers, err := p.extractMailers()
	if err != nil {
		return nil, fmt.Errorf("failed to extract mailers: %w", err)
	}
	conf.Mailers = mailers

	// Extract caches
	caches, err := p.extractCaches()
	if err != nil {
		return nil, fmt.Errorf("failed to extract caches: %w", err)
	}
	conf.Caches = caches

	// Extract rings
	rings, err := p.extractRings()
	if err != nil {
		return nil, fmt.Errorf("failed to extract rings: %w", err)
	}
	conf.Rings = rings

	// Extract http-errors sections
	httpErrors, err := p.extractHTTPErrors()
	if err != nil {
		return nil, fmt.Errorf("failed to extract http-errors: %w", err)
	}
	conf.HTTPErrors = httpErrors

	// Extract userlists
	userlists, err := p.extractUserlists()
	if err != nil {
		return nil, fmt.Errorf("failed to extract userlists: %w", err)
	}
	conf.Userlists = userlists

	// Extract programs
	programs, err := p.extractPrograms()
	if err != nil {
		return nil, fmt.Errorf("failed to extract programs: %w", err)
	}
	conf.Programs = programs

	// Extract log-forwards
	logForwards, err := p.extractLogForwards()
	if err != nil {
		return nil, fmt.Errorf("failed to extract log-forwards: %w", err)
	}
	conf.LogForwards = logForwards

	// Extract fcgi-apps
	fcgiApps, err := p.extractFCGIApps()
	if err != nil {
		return nil, fmt.Errorf("failed to extract fcgi-apps: %w", err)
	}
	conf.FCGIApps = fcgiApps

	// Extract crt-stores
	crtStores, err := p.extractCrtStores()
	if err != nil {
		return nil, fmt.Errorf("failed to extract crt-stores: %w", err)
	}
	conf.CrtStores = crtStores

	return conf, nil
}

// extractGlobal extracts the global section using client-native's ParseGlobalSection.
//
// This automatically handles ALL global fields (100+ fields including maxconn, daemon,
// nbproc, nbthread, pidfile, stats sockets, chroot, user, group, tune options, SSL options,
// performance options, lua options, etc.) and all nested structures (PerformanceOptions,
// TuneOptions, LogTargets, etc.) without manual handling.
func (p *Parser) extractGlobal() (*models.Global, error) {
	// ParseGlobalSection handles the complete Global section including all nested structures
	global, err := configuration.ParseGlobalSection(p.parser)
	if err != nil {
		return nil, fmt.Errorf("failed to parse global section: %w", err)
	}

	// Parse log targets separately (nested structure)
	// Global section has no name (empty string)
	logTargets, err := configuration.ParseLogTargets(string(parser.Global), "", p.parser)
	if err == nil {
		global.LogTargetList = logTargets
	}

	return global, nil
}

// extractDefaults extracts all defaults sections using client-native's ParseSection.
//
// This automatically handles ALL defaults fields (60+ fields including mode, maxconn,
// timeout settings, log settings, options like httplog/dontlognull/forwardfor,
// error handling, compression, etc.) without manual type assertions.
func (p *Parser) extractDefaults() ([]*models.Defaults, error) {
	sections, err := p.parser.SectionsGet(parser.Defaults)
	if err != nil {
		// No defaults sections is valid
		return nil, nil
	}

	defaults := make([]*models.Defaults, 0, len(sections))
	for _, sectionName := range sections {
		def := &models.Defaults{}

		// ParseSection handles ALL DefaultsBase fields automatically (60+ fields)
		if err := configuration.ParseSection(&def.DefaultsBase, parser.Defaults, sectionName, p.parser); err != nil {
			slog.Warn("Failed to parse defaults section", "section", sectionName, "error", err)
			continue
		}
		def.Name = sectionName

		// Parse log targets separately (nested structure)
		logTargets, err := configuration.ParseLogTargets(string(parser.Defaults), sectionName, p.parser)
		if err == nil {
			def.LogTargetList = logTargets
		}

		defaults = append(defaults, def)
	}

	return defaults, nil
}

// extractFrontends extracts all frontend sections using client-native's Parse* functions.
//
// This automatically handles ALL frontend fields (80+ fields) and nested structures
// (binds, ACLs, HTTP/TCP rules, filters, log targets, etc.) using specialized Parse* helpers.
func (p *Parser) extractFrontends() ([]*models.Frontend, error) {
	sections, err := p.parser.SectionsGet(parser.Frontends)
	if err != nil {
		// No frontends is valid
		return nil, nil
	}

	frontends := make([]*models.Frontend, 0, len(sections))
	for _, sectionName := range sections {
		fe := &models.Frontend{}

		// ParseSection handles ALL FrontendBase fields automatically (80+ fields:
		// mode, maxconn, default_backend, timeouts, compression, forwardfor, httplog, etc.)
		if err := configuration.ParseSection(&fe.FrontendBase, parser.Frontends, sectionName, p.parser); err != nil {
			slog.Warn("Failed to parse frontend section", "section", sectionName, "error", err)
			continue
		}
		fe.Name = sectionName

		// Parse nested structures using client-native's Parse* helpers
		fe.ACLList, _ = configuration.ParseACLs(parser.Frontends, sectionName, p.parser)
		// Note: Binds returns slice but fe.Binds is map - conversion needed or use ParseSection
		binds, _ := configuration.ParseBinds(string(parser.Frontends), sectionName, p.parser)
		if binds != nil {
			fe.Binds = make(map[string]models.Bind)
			for _, bind := range binds {
				if bind != nil {
					fe.Binds[bind.Name] = *bind
				}
			}
		}
		fe.HTTPRequestRuleList, _ = configuration.ParseHTTPRequestRules(string(parser.Frontends), sectionName, p.parser)
		fe.HTTPResponseRuleList, _ = configuration.ParseHTTPResponseRules(string(parser.Frontends), sectionName, p.parser)
		fe.TCPRequestRuleList, _ = configuration.ParseTCPRequestRules(string(parser.Frontends), sectionName, p.parser)
		fe.HTTPAfterResponseRuleList, _ = configuration.ParseHTTPAfterRules(string(parser.Frontends), sectionName, p.parser)
		fe.HTTPErrorRuleList, _ = configuration.ParseHTTPErrorRules(string(parser.Frontends), sectionName, p.parser)
		fe.FilterList, _ = configuration.ParseFilters(string(parser.Frontends), sectionName, p.parser)
		fe.LogTargetList, _ = configuration.ParseLogTargets(string(parser.Frontends), sectionName, p.parser)
		fe.BackendSwitchingRuleList, _ = configuration.ParseBackendSwitchingRules(sectionName, p.parser)
		fe.CaptureList, _ = configuration.ParseDeclareCaptures(sectionName, p.parser)

		frontends = append(frontends, fe)
	}

	return frontends, nil
}

// extractBackends extracts all backend sections using client-native's Parse* functions.
//
// This automatically handles ALL backend fields (100+ fields) and nested structures
// (servers, ACLs, HTTP/TCP rules, filters, stick rules, health checks, etc.)
// using specialized Parse* helpers.
func (p *Parser) extractBackends() ([]*models.Backend, error) {
	sections, err := p.parser.SectionsGet(parser.Backends)
	if err != nil {
		// No backends is valid
		return nil, nil
	}

	backends := make([]*models.Backend, 0, len(sections))
	for _, sectionName := range sections {
		be := &models.Backend{}

		// ParseSection handles ALL BackendBase fields automatically (100+ fields:
		// mode, balance, timeouts, cookie, compression, forwardfor, httpchk, etc.)
		if err := configuration.ParseSection(&be.BackendBase, parser.Backends, sectionName, p.parser); err != nil {
			slog.Warn("Failed to parse backend section", "section", sectionName, "error", err)
			continue
		}
		be.Name = sectionName

		// Parse nested structures using client-native's Parse* helpers
		be.ACLList, _ = configuration.ParseACLs(parser.Backends, sectionName, p.parser)

		// Convert Servers slice to map
		servers, _ := configuration.ParseServers(string(parser.Backends), sectionName, p.parser)
		if servers != nil {
			be.Servers = make(map[string]models.Server)
			for _, server := range servers {
				if server != nil {
					be.Servers[server.Name] = *server
				}
			}
		}

		be.HTTPRequestRuleList, _ = configuration.ParseHTTPRequestRules(string(parser.Backends), sectionName, p.parser)
		be.HTTPResponseRuleList, _ = configuration.ParseHTTPResponseRules(string(parser.Backends), sectionName, p.parser)
		be.TCPRequestRuleList, _ = configuration.ParseTCPRequestRules(string(parser.Backends), sectionName, p.parser)
		be.TCPResponseRuleList, _ = configuration.ParseTCPResponseRules(string(parser.Backends), sectionName, p.parser)
		be.FilterList, _ = configuration.ParseFilters(string(parser.Backends), sectionName, p.parser)
		be.LogTargetList, _ = configuration.ParseLogTargets(string(parser.Backends), sectionName, p.parser)
		be.HTTPAfterResponseRuleList, _ = configuration.ParseHTTPAfterRules(string(parser.Backends), sectionName, p.parser)
		be.HTTPErrorRuleList, _ = configuration.ParseHTTPErrorRules(string(parser.Backends), sectionName, p.parser)
		be.HTTPCheckList, _ = configuration.ParseHTTPChecks(string(parser.Backends), sectionName, p.parser)
		be.TCPCheckRuleList, _ = configuration.ParseTCPChecks(string(parser.Backends), sectionName, p.parser)
		be.StickRuleList, _ = configuration.ParseStickRules(sectionName, p.parser)
		be.ServerSwitchingRuleList, _ = configuration.ParseServerSwitchingRules(sectionName, p.parser)

		// Convert ServerTemplates slice to map
		serverTemplates, _ := configuration.ParseServerTemplates(sectionName, p.parser)
		if serverTemplates != nil {
			be.ServerTemplates = make(map[string]models.ServerTemplate)
			for _, template := range serverTemplates {
				if template != nil {
					be.ServerTemplates[template.Prefix] = *template
				}
			}
		}

		backends = append(backends, be)
	}

	return backends, nil
}

// extractPeers extracts all peers sections using client-native's Parse* functions.
func (p *Parser) extractPeers() ([]*models.PeerSection, error) {
	sections, err := p.parser.SectionsGet(parser.Peers)
	if err != nil {
		// No peers sections is valid
		return nil, nil
	}

	peers := make([]*models.PeerSection, 0, len(sections))
	for _, sectionName := range sections {
		peer := &models.PeerSection{}

		// ParseSection handles all peer section fields
		if err := configuration.ParseSection(peer, parser.Peers, sectionName, p.parser); err != nil {
			slog.Warn("Failed to parse peers section", "section", sectionName, "error", err)
			continue
		}
		peer.Name = sectionName

		// Convert PeerEntries slice to map
		peerEntries, _ := configuration.ParsePeerEntries(sectionName, p.parser)
		if peerEntries != nil {
			peer.PeerEntries = make(map[string]models.PeerEntry)
			for _, entry := range peerEntries {
				if entry != nil {
					peer.PeerEntries[entry.Name] = *entry
				}
			}
		}

		peers = append(peers, peer)
	}

	return peers, nil
}

// extractResolvers extracts all resolvers sections using client-native's ParseResolverSection.
func (p *Parser) extractResolvers() ([]*models.Resolver, error) {
	sections, err := p.parser.SectionsGet(parser.Resolvers)
	if err != nil {
		// No resolvers sections is valid
		return nil, nil
	}

	resolvers := make([]*models.Resolver, 0, len(sections))
	for _, sectionName := range sections {
		resolver := &models.Resolver{}
		resolver.Name = sectionName

		// ParseResolverSection handles all resolver fields automatically
		if err := configuration.ParseResolverSection(p.parser, resolver); err != nil {
			slog.Warn("Failed to parse resolvers section", "section", sectionName, "error", err)
			continue
		}

		// Convert Nameservers slice to map
		nameservers, _ := configuration.ParseNameservers(sectionName, p.parser)
		if nameservers != nil {
			resolver.Nameservers = make(map[string]models.Nameserver)
			for _, ns := range nameservers {
				if ns != nil {
					resolver.Nameservers[ns.Name] = *ns
				}
			}
		}

		resolvers = append(resolvers, resolver)
	}

	return resolvers, nil
}

// extractMailers extracts all mailers sections using client-native's ParseMailersSection.
func (p *Parser) extractMailers() ([]*models.MailersSection, error) {
	sections, err := p.parser.SectionsGet(parser.Mailers)
	if err != nil {
		// No mailers sections is valid
		return nil, nil
	}

	mailers := make([]*models.MailersSection, 0, len(sections))
	for _, sectionName := range sections {
		mailer := &models.MailersSection{}
		mailer.Name = sectionName

		// ParseMailersSection handles all mailer fields automatically
		if err := configuration.ParseMailersSection(p.parser, mailer); err != nil {
			slog.Warn("Failed to parse mailers section", "section", sectionName, "error", err)
			continue
		}

		// Convert MailerEntries slice to map
		mailerEntries, _ := configuration.ParseMailerEntries(sectionName, p.parser)
		if mailerEntries != nil {
			mailer.MailerEntries = make(map[string]models.MailerEntry)
			for _, entry := range mailerEntries {
				if entry != nil {
					mailer.MailerEntries[entry.Name] = *entry
				}
			}
		}

		mailers = append(mailers, mailer)
	}

	return mailers, nil
}

// extractCaches extracts all cache sections using client-native's ParseCacheSection.
func (p *Parser) extractCaches() ([]*models.Cache, error) {
	sections, err := p.parser.SectionsGet(parser.Cache)
	if err != nil {
		// No cache sections is valid
		return nil, nil
	}

	caches := make([]*models.Cache, 0, len(sections))
	for _, sectionName := range sections {
		cache := &models.Cache{}
		name := sectionName
		cache.Name = &name

		// ParseCacheSection handles all cache fields automatically
		if err := configuration.ParseCacheSection(p.parser, cache); err != nil {
			slog.Warn("Failed to parse cache section", "section", sectionName, "error", err)
			continue
		}

		caches = append(caches, cache)
	}

	return caches, nil
}

// extractRings extracts all ring sections using client-native's ParseRingSection.
func (p *Parser) extractRings() ([]*models.Ring, error) {
	sections, err := p.parser.SectionsGet(parser.Ring)
	if err != nil {
		// No ring sections is valid
		return nil, nil
	}

	rings := make([]*models.Ring, 0, len(sections))
	for _, sectionName := range sections {
		ring := &models.Ring{}
		ring.Name = sectionName

		// ParseRingSection handles all ring fields automatically
		if err := configuration.ParseRingSection(p.parser, ring); err != nil {
			slog.Warn("Failed to parse ring section", "section", sectionName, "error", err)
			continue
		}

		rings = append(rings, ring)
	}

	return rings, nil
}

// extractHTTPErrors extracts all http-errors sections using client-native's Parse* functions.
func (p *Parser) extractHTTPErrors() ([]*models.HTTPErrorsSection, error) {
	sections, err := p.parser.SectionsGet(parser.HTTPErrors)
	if err != nil {
		// No http-errors sections is valid
		return nil, nil
	}

	httpErrors := make([]*models.HTTPErrorsSection, 0, len(sections))
	for _, sectionName := range sections {
		// ParseHTTPErrorsSection handles complete parsing including ErrorFiles
		httpError, err := configuration.ParseHTTPErrorsSection(p.parser, sectionName)
		if err != nil {
			// Log error but continue with other sections
			continue
		}

		httpErrors = append(httpErrors, httpError)
	}

	return httpErrors, nil
}

// extractUserlists extracts all userlist sections using client-native's Parse* functions.
// Userlists contain users and groups for authentication.
func (p *Parser) extractUserlists() ([]*models.Userlist, error) {
	sections, err := p.parser.SectionsGet(parser.UserList)
	if err != nil {
		// No userlist sections is valid
		return nil, nil
	}

	userlists := make([]*models.Userlist, 0, len(sections))
	for _, sectionName := range sections {
		userlist := &models.Userlist{}

		// Parse userlist base section
		if err := configuration.ParseSection(&userlist.UserlistBase, parser.UserList, sectionName, p.parser); err != nil {
			slog.Warn("Failed to parse userlist section", "section", sectionName, "error", err)
			continue
		}

		// Parse users within this userlist
		users, err := configuration.ParseUsers(sectionName, p.parser)
		if err == nil && users != nil {
			userlist.Users = make(map[string]models.User)
			for _, user := range users {
				if user != nil && user.Username != "" {
					userlist.Users[user.Username] = *user
				}
			}
		}

		// Parse groups within this userlist
		groups, err := configuration.ParseGroups(sectionName, p.parser)
		if err == nil && groups != nil {
			userlist.Groups = make(map[string]models.Group)
			for _, group := range groups {
				if group != nil && group.Name != "" {
					userlist.Groups[group.Name] = *group
				}
			}
		}

		userlists = append(userlists, userlist)
	}

	return userlists, nil
}

// extractPrograms extracts all program sections using client-native's ParseProgram.
// Programs are external processes managed by HAProxy.
func (p *Parser) extractPrograms() ([]*models.Program, error) {
	sections, err := p.parser.SectionsGet(parser.Program)
	if err != nil {
		// No program sections is valid
		return nil, nil
	}

	programs := make([]*models.Program, 0, len(sections))
	for _, sectionName := range sections {
		// ParseProgram handles all program fields automatically
		program, err := configuration.ParseProgram(p.parser, sectionName)
		if err != nil {
			slog.Warn("Failed to parse program section", "section", sectionName, "error", err)
			continue
		}

		programs = append(programs, program)
	}

	return programs, nil
}

// extractLogForwards extracts all log-forward sections using client-native's ParseLogForward.
// Log-forwards define log forwarding rules.
func (p *Parser) extractLogForwards() ([]*models.LogForward, error) {
	sections, err := p.parser.SectionsGet(parser.LogForward)
	if err != nil {
		// No log-forward sections is valid
		return nil, nil
	}

	logForwards := make([]*models.LogForward, 0, len(sections))
	for _, sectionName := range sections {
		// ParseLogForward takes a pointer to fill
		logForward := &models.LogForward{
			LogForwardBase: models.LogForwardBase{Name: sectionName},
		}
		if err := configuration.ParseLogForward(p.parser, logForward); err != nil {
			slog.Warn("Failed to parse log-forward section", "section", sectionName, "error", err)
			continue
		}

		logForwards = append(logForwards, logForward)
	}

	return logForwards, nil
}

// extractFCGIApps extracts all fcgi-app sections using client-native's ParseFCGIApp.
// FCGI apps define FastCGI application configurations.
func (p *Parser) extractFCGIApps() ([]*models.FCGIApp, error) {
	sections, err := p.parser.SectionsGet(parser.FCGIApp)
	if err != nil {
		// No fcgi-app sections is valid
		return nil, nil
	}

	fcgiApps := make([]*models.FCGIApp, 0, len(sections))
	for _, sectionName := range sections {
		// ParseFCGIApp handles all fields automatically
		fcgiApp, err := configuration.ParseFCGIApp(p.parser, sectionName)
		if err != nil {
			slog.Warn("Failed to parse fcgi-app section", "section", sectionName, "error", err)
			continue
		}

		fcgiApps = append(fcgiApps, fcgiApp)
	}

	return fcgiApps, nil
}

// extractCrtStores extracts all crt-store sections using client-native's ParseCrtStore.
// Certificate stores define locations for SSL certificates.
func (p *Parser) extractCrtStores() ([]*models.CrtStore, error) {
	sections, err := p.parser.SectionsGet(parser.CrtStore)
	if err != nil {
		// No crt-store sections is valid
		return nil, nil
	}

	crtStores := make([]*models.CrtStore, 0, len(sections))
	for _, sectionName := range sections {
		// ParseCrtStore handles all fields automatically
		crtStore, err := configuration.ParseCrtStore(p.parser, sectionName)
		if err != nil {
			slog.Warn("Failed to parse crt-store section", "section", sectionName, "error", err)
			continue
		}

		crtStores = append(crtStores, crtStore)
	}

	return crtStores, nil
}
