package comparator

import (
	"github.com/haproxytech/client-native/v6/models"

	"haproxy-template-ic/pkg/dataplane/comparator/sections"
	"haproxy-template-ic/pkg/dataplane/parser"
)

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
		return []Operation{sections.NewLogTargetFrontendCreate(parentName, logTarget, index)}
	}
	return []Operation{sections.NewLogTargetBackendCreate(parentName, logTarget, index)}
}

func (c *Comparator) deleteLogTargetOperation(parentType, parentName string, logTarget *models.LogTarget, index int) []Operation {
	if parentType == parentTypeFrontend {
		return []Operation{sections.NewLogTargetFrontendDelete(parentName, logTarget, index)}
	}
	return []Operation{sections.NewLogTargetBackendDelete(parentName, logTarget, index)}
}

func (c *Comparator) updateLogTargetOperation(parentType, parentName string, currentLog, desiredLog *models.LogTarget, index int) []Operation {
	if !currentLog.Equal(*desiredLog) {
		if parentType == parentTypeFrontend {
			return []Operation{sections.NewLogTargetFrontendUpdate(parentName, desiredLog, index)}
		}
		return []Operation{sections.NewLogTargetBackendUpdate(parentName, desiredLog, index)}
	}
	return nil
}

// compareLogForwards compares log-forward sections between current and desired configurations.
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
			operations = append(operations, sections.NewLogForwardCreate(logForward))
		}
	}

	// Find deleted log-forward sections
	for name, logForward := range currentMap {
		if _, exists := desiredMap[name]; !exists {
			operations = append(operations, sections.NewLogForwardDelete(logForward))
		}
	}

	// Find modified log-forward sections
	for name, desiredLogForward := range desiredMap {
		if currentLogForward, exists := currentMap[name]; exists {
			if !logForwardEqual(currentLogForward, desiredLogForward) {
				operations = append(operations, sections.NewLogForwardUpdate(desiredLogForward))
			}
		}
	}

	return operations
}

// logForwardEqual compares two log-forward sections for equality.
func logForwardEqual(l1, l2 *models.LogForward) bool {
	return l1.Equal(*l2)
}
