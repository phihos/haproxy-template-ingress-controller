// Copyright 2025 Philipp Hossner
//
// Licensed under the Apache License, Version 2.0 (the "License");
// you may not use this file except in compliance with the License.
// You may obtain a copy of the License at
//
//     http://www.apache.org/licenses/LICENSE-2.0
//
// Unless required by applicable law or agreed to in writing, software
// distributed under the License is distributed on an "AS IS" BASIS,
// WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
// See the License for the specific language governing permissions and
// limitations under the License.

package renderer

import (
	"testing"

	"github.com/stretchr/testify/assert"

	"haproxy-template-ic/pkg/core/config"
)

func TestSortSnippetsByPriority(t *testing.T) {
	tests := []struct {
		name     string
		snippets map[string]config.TemplateSnippet
		want     []string
	}{
		{
			name: "sort by priority ascending",
			snippets: map[string]config.TemplateSnippet{
				"high":   {Name: "high", Priority: 100},
				"medium": {Name: "medium", Priority: 500},
				"low":    {Name: "low", Priority: 900},
			},
			want: []string{"high", "medium", "low"},
		},
		{
			name: "same priority sorts alphabetically",
			snippets: map[string]config.TemplateSnippet{
				"charlie": {Name: "charlie", Priority: 100},
				"alpha":   {Name: "alpha", Priority: 100},
				"bravo":   {Name: "bravo", Priority: 100},
			},
			want: []string{"alpha", "bravo", "charlie"},
		},
		{
			name: "zero priority defaults to 500",
			snippets: map[string]config.TemplateSnippet{
				"explicit-500": {Name: "explicit-500", Priority: 500},
				"default":      {Name: "default", Priority: 0},
				"low":          {Name: "low", Priority: 600},
				"high":         {Name: "high", Priority: 400},
			},
			want: []string{"high", "default", "explicit-500", "low"},
		},
		{
			name: "mixed priority and alphabetical",
			snippets: map[string]config.TemplateSnippet{
				"backend-annotation-500-haproxytech-auth":  {Priority: 500},
				"backend-annotation-100-rate-limit":        {Priority: 100},
				"top-level-annotation-500-haproxytech-tls": {Priority: 500},
				"backend-annotation-500-cors":              {Priority: 500},
			},
			want: []string{
				"backend-annotation-100-rate-limit",
				"backend-annotation-500-cors",
				"backend-annotation-500-haproxytech-auth",
				"top-level-annotation-500-haproxytech-tls",
			},
		},
		{
			name:     "empty snippets",
			snippets: map[string]config.TemplateSnippet{},
			want:     []string{},
		},
		{
			name: "single snippet",
			snippets: map[string]config.TemplateSnippet{
				"only": {Name: "only", Priority: 100},
			},
			want: []string{"only"},
		},
		{
			name: "all default priority",
			snippets: map[string]config.TemplateSnippet{
				"zebra":   {Name: "zebra"},
				"alpha":   {Name: "alpha"},
				"charlie": {Name: "charlie"},
			},
			want: []string{"alpha", "charlie", "zebra"},
		},
		{
			name: "negative priorities",
			snippets: map[string]config.TemplateSnippet{
				"negative": {Name: "negative", Priority: -100},
				"zero":     {Name: "zero", Priority: 0}, // 0 defaults to 500
				"positive": {Name: "positive", Priority: 100},
			},
			want: []string{"negative", "positive", "zero"}, // zero has default priority 500
		},
		{
			name: "real-world annotation snippet ordering",
			snippets: map[string]config.TemplateSnippet{
				"backend-annotation-500-haproxytech-auth":   {Priority: 500},
				"backend-annotation-200-rate-limit":         {Priority: 200},
				"backend-annotation-800-logging":            {Priority: 800},
				"top-level-annotation-500-haproxytech-auth": {Priority: 500},
				"top-level-annotation-100-global-config":    {Priority: 100},
				"backend-annotation-500-cors":               {Priority: 500},
				"backend-annotation-500-compression":        {Priority: 500},
			},
			want: []string{
				"top-level-annotation-100-global-config",
				"backend-annotation-200-rate-limit",
				"backend-annotation-500-compression",
				"backend-annotation-500-cors",
				"backend-annotation-500-haproxytech-auth",
				"top-level-annotation-500-haproxytech-auth",
				"backend-annotation-800-logging",
			},
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			got := sortSnippetsByPriority(tt.snippets)
			assert.Equal(t, tt.want, got)
		})
	}
}
