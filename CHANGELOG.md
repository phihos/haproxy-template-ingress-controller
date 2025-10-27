# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- **Leader election for high availability**: Multiple controller replicas now supported with automatic leader election
  - Only the leader replica deploys configurations to HAProxy instances
  - All replicas continue watching resources, rendering templates, and validating configs (hot standby)
  - Automatic failover when leader fails (~15-20 seconds downtime)
  - Configurable timing parameters for failover speed and clock skew tolerance
  - Default deployment now uses 2 replicas for HA

- **Leader election metrics**: Three new Prometheus metrics for monitoring leadership
  - `haproxy_ic_leader_election_is_leader`: Current leadership status (gauge)
  - `haproxy_ic_leader_election_transitions_total`: Total leadership transitions (counter)
  - `haproxy_ic_leader_election_time_as_leader_seconds_total`: Cumulative time as leader (counter)

- **Leader election events**: Four new event types for observability
  - `LeaderElectionStartedEvent`: Published when leader election starts
  - `BecameLeaderEvent`: Published when replica becomes leader
  - `LostLeadershipEvent`: Published when replica loses leadership
  - `NewLeaderObservedEvent`: Published when new leader is observed

- **High availability operations guide**: Comprehensive documentation in `docs/operations/high-availability.md`
  - Configuration and deployment instructions
  - Leadership monitoring and troubleshooting
  - Best practices for production deployments
  - Migration guide from single-replica

### Changed

- **Default replica count changed from 1 to 2**: Helm chart now deploys 2 replicas by default for HA
- **Updated Helm chart**: Added POD_NAME and POD_NAMESPACE environment variables via downward API
- **Updated RBAC**: Added permissions for coordination.k8s.io/v1 Lease resources

### Fixed

- Fixed disabled mode in leader election to properly track state and publish events
