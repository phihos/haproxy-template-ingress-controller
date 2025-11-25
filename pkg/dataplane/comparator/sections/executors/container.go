// Package executors provides pre-built executor functions for HAProxy configuration operations.
package executors

import (
	"context"
	"net/http"

	"haproxy-template-ic/pkg/dataplane/client"
	"haproxy-template-ic/pkg/generated/dataplaneapi"
	v30 "haproxy-template-ic/pkg/generated/dataplaneapi/v30"
	v31 "haproxy-template-ic/pkg/generated/dataplaneapi/v31"
	v32 "haproxy-template-ic/pkg/generated/dataplaneapi/v32"
)

// =============================================================================
// User Executors (Userlist container)
// =============================================================================

// UserCreate returns an executor for creating users in userlists.
func UserCreate(userlistName string) func(ctx context.Context, c *client.DataplaneClient, txID string, containerName string, childName string, model *dataplaneapi.User) error {
	return func(ctx context.Context, c *client.DataplaneClient, txID string, _ string, _ string, model *dataplaneapi.User) error {
		params := &dataplaneapi.CreateUserParams{
			TransactionId: &txID,
			Userlist:      userlistName,
		}
		clientset := c.Clientset()

		resp, err := client.DispatchCreate(ctx, c, model,
			func(m v32.User, _ *v32.CreateUserParams) (*http.Response, error) {
				return clientset.V32().CreateUser(ctx, (*v32.CreateUserParams)(params), m)
			},
			func(m v31.User, _ *v31.CreateUserParams) (*http.Response, error) {
				return clientset.V31().CreateUser(ctx, (*v31.CreateUserParams)(params), m)
			},
			func(m v30.User, _ *v30.CreateUserParams) (*http.Response, error) {
				return clientset.V30().CreateUser(ctx, (*v30.CreateUserParams)(params), m)
			},
			(*v32.CreateUserParams)(params),
			(*v31.CreateUserParams)(params),
			(*v30.CreateUserParams)(params),
		)
		if err != nil {
			return err
		}
		defer resp.Body.Close()
		return client.CheckResponse(resp, "user creation")
	}
}

// UserUpdate returns an executor for updating users in userlists.
func UserUpdate(userlistName string) func(ctx context.Context, c *client.DataplaneClient, txID string, containerName string, childName string, model *dataplaneapi.User) error {
	return func(ctx context.Context, c *client.DataplaneClient, txID string, _ string, childName string, model *dataplaneapi.User) error {
		params := &dataplaneapi.ReplaceUserParams{
			TransactionId: &txID,
			Userlist:      userlistName,
		}
		clientset := c.Clientset()

		resp, err := client.DispatchUpdate(ctx, c, childName, model,
			func(name string, m v32.User, _ *v32.ReplaceUserParams) (*http.Response, error) {
				return clientset.V32().ReplaceUser(ctx, name, (*v32.ReplaceUserParams)(params), m)
			},
			func(name string, m v31.User, _ *v31.ReplaceUserParams) (*http.Response, error) {
				return clientset.V31().ReplaceUser(ctx, name, (*v31.ReplaceUserParams)(params), m)
			},
			func(name string, m v30.User, _ *v30.ReplaceUserParams) (*http.Response, error) {
				return clientset.V30().ReplaceUser(ctx, name, (*v30.ReplaceUserParams)(params), m)
			},
			(*v32.ReplaceUserParams)(params),
			(*v31.ReplaceUserParams)(params),
			(*v30.ReplaceUserParams)(params),
		)
		if err != nil {
			return err
		}
		defer resp.Body.Close()
		return client.CheckResponse(resp, "user update")
	}
}

// UserDelete returns an executor for deleting users from userlists.
func UserDelete(userlistName string) func(ctx context.Context, c *client.DataplaneClient, txID string, containerName string, childName string, model *dataplaneapi.User) error {
	return func(ctx context.Context, c *client.DataplaneClient, txID string, _ string, childName string, _ *dataplaneapi.User) error {
		params := &dataplaneapi.DeleteUserParams{
			TransactionId: &txID,
			Userlist:      userlistName,
		}
		clientset := c.Clientset()

		resp, err := client.DispatchDelete(ctx, c, childName,
			func(name string, _ *v32.DeleteUserParams) (*http.Response, error) {
				return clientset.V32().DeleteUser(ctx, name, (*v32.DeleteUserParams)(params))
			},
			func(name string, _ *v31.DeleteUserParams) (*http.Response, error) {
				return clientset.V31().DeleteUser(ctx, name, (*v31.DeleteUserParams)(params))
			},
			func(name string, _ *v30.DeleteUserParams) (*http.Response, error) {
				return clientset.V30().DeleteUser(ctx, name, (*v30.DeleteUserParams)(params))
			},
			(*v32.DeleteUserParams)(params),
			(*v31.DeleteUserParams)(params),
			(*v30.DeleteUserParams)(params),
		)
		if err != nil {
			return err
		}
		defer resp.Body.Close()
		return client.CheckResponse(resp, "user deletion")
	}
}

// =============================================================================
// Mailer Entry Executors (Mailers container)
// =============================================================================

// MailerEntryCreate returns an executor for creating mailer entries in mailers sections.
func MailerEntryCreate(mailersName string) func(ctx context.Context, c *client.DataplaneClient, txID string, containerName string, childName string, model *dataplaneapi.MailerEntry) error {
	return func(ctx context.Context, c *client.DataplaneClient, txID string, _ string, _ string, model *dataplaneapi.MailerEntry) error {
		params := &dataplaneapi.CreateMailerEntryParams{
			TransactionId:  &txID,
			MailersSection: mailersName,
		}
		clientset := c.Clientset()

		resp, err := client.DispatchCreate(ctx, c, model,
			func(m v32.MailerEntry, _ *v32.CreateMailerEntryParams) (*http.Response, error) {
				return clientset.V32().CreateMailerEntry(ctx, (*v32.CreateMailerEntryParams)(params), m)
			},
			func(m v31.MailerEntry, _ *v31.CreateMailerEntryParams) (*http.Response, error) {
				return clientset.V31().CreateMailerEntry(ctx, (*v31.CreateMailerEntryParams)(params), m)
			},
			func(m v30.MailerEntry, _ *v30.CreateMailerEntryParams) (*http.Response, error) {
				return clientset.V30().CreateMailerEntry(ctx, (*v30.CreateMailerEntryParams)(params), m)
			},
			(*v32.CreateMailerEntryParams)(params),
			(*v31.CreateMailerEntryParams)(params),
			(*v30.CreateMailerEntryParams)(params),
		)
		if err != nil {
			return err
		}
		defer resp.Body.Close()
		return client.CheckResponse(resp, "mailer entry creation")
	}
}

// MailerEntryUpdate returns an executor for updating mailer entries in mailers sections.
func MailerEntryUpdate(mailersName string) func(ctx context.Context, c *client.DataplaneClient, txID string, containerName string, childName string, model *dataplaneapi.MailerEntry) error {
	return func(ctx context.Context, c *client.DataplaneClient, txID string, _ string, childName string, model *dataplaneapi.MailerEntry) error {
		params := &dataplaneapi.ReplaceMailerEntryParams{
			TransactionId:  &txID,
			MailersSection: mailersName,
		}
		clientset := c.Clientset()

		resp, err := client.DispatchUpdate(ctx, c, childName, model,
			func(name string, m v32.MailerEntry, _ *v32.ReplaceMailerEntryParams) (*http.Response, error) {
				return clientset.V32().ReplaceMailerEntry(ctx, name, (*v32.ReplaceMailerEntryParams)(params), m)
			},
			func(name string, m v31.MailerEntry, _ *v31.ReplaceMailerEntryParams) (*http.Response, error) {
				return clientset.V31().ReplaceMailerEntry(ctx, name, (*v31.ReplaceMailerEntryParams)(params), m)
			},
			func(name string, m v30.MailerEntry, _ *v30.ReplaceMailerEntryParams) (*http.Response, error) {
				return clientset.V30().ReplaceMailerEntry(ctx, name, (*v30.ReplaceMailerEntryParams)(params), m)
			},
			(*v32.ReplaceMailerEntryParams)(params),
			(*v31.ReplaceMailerEntryParams)(params),
			(*v30.ReplaceMailerEntryParams)(params),
		)
		if err != nil {
			return err
		}
		defer resp.Body.Close()
		return client.CheckResponse(resp, "mailer entry update")
	}
}

// MailerEntryDelete returns an executor for deleting mailer entries from mailers sections.
func MailerEntryDelete(mailersName string) func(ctx context.Context, c *client.DataplaneClient, txID string, containerName string, childName string, model *dataplaneapi.MailerEntry) error {
	return func(ctx context.Context, c *client.DataplaneClient, txID string, _ string, childName string, _ *dataplaneapi.MailerEntry) error {
		params := &dataplaneapi.DeleteMailerEntryParams{
			TransactionId:  &txID,
			MailersSection: mailersName,
		}
		clientset := c.Clientset()

		resp, err := client.DispatchDelete(ctx, c, childName,
			func(name string, _ *v32.DeleteMailerEntryParams) (*http.Response, error) {
				return clientset.V32().DeleteMailerEntry(ctx, name, (*v32.DeleteMailerEntryParams)(params))
			},
			func(name string, _ *v31.DeleteMailerEntryParams) (*http.Response, error) {
				return clientset.V31().DeleteMailerEntry(ctx, name, (*v31.DeleteMailerEntryParams)(params))
			},
			func(name string, _ *v30.DeleteMailerEntryParams) (*http.Response, error) {
				return clientset.V30().DeleteMailerEntry(ctx, name, (*v30.DeleteMailerEntryParams)(params))
			},
			(*v32.DeleteMailerEntryParams)(params),
			(*v31.DeleteMailerEntryParams)(params),
			(*v30.DeleteMailerEntryParams)(params),
		)
		if err != nil {
			return err
		}
		defer resp.Body.Close()
		return client.CheckResponse(resp, "mailer entry deletion")
	}
}

// =============================================================================
// Peer Entry Executors (Peer container)
// =============================================================================

// PeerEntryCreate returns an executor for creating peer entries in peers sections.
func PeerEntryCreate(peerSectionName string) func(ctx context.Context, c *client.DataplaneClient, txID string, containerName string, childName string, model *dataplaneapi.PeerEntry) error {
	return func(ctx context.Context, c *client.DataplaneClient, txID string, _ string, _ string, model *dataplaneapi.PeerEntry) error {
		params := &dataplaneapi.CreatePeerEntryParams{
			TransactionId: &txID,
			PeerSection:   peerSectionName,
		}
		clientset := c.Clientset()

		resp, err := client.DispatchCreate(ctx, c, model,
			func(m v32.PeerEntry, _ *v32.CreatePeerEntryParams) (*http.Response, error) {
				return clientset.V32().CreatePeerEntry(ctx, (*v32.CreatePeerEntryParams)(params), m)
			},
			func(m v31.PeerEntry, _ *v31.CreatePeerEntryParams) (*http.Response, error) {
				return clientset.V31().CreatePeerEntry(ctx, (*v31.CreatePeerEntryParams)(params), m)
			},
			func(m v30.PeerEntry, _ *v30.CreatePeerEntryParams) (*http.Response, error) {
				return clientset.V30().CreatePeerEntry(ctx, (*v30.CreatePeerEntryParams)(params), m)
			},
			(*v32.CreatePeerEntryParams)(params),
			(*v31.CreatePeerEntryParams)(params),
			(*v30.CreatePeerEntryParams)(params),
		)
		if err != nil {
			return err
		}
		defer resp.Body.Close()
		return client.CheckResponse(resp, "peer entry creation")
	}
}

// PeerEntryUpdate returns an executor for updating peer entries in peers sections.
func PeerEntryUpdate(peerSectionName string) func(ctx context.Context, c *client.DataplaneClient, txID string, containerName string, childName string, model *dataplaneapi.PeerEntry) error {
	return func(ctx context.Context, c *client.DataplaneClient, txID string, _ string, childName string, model *dataplaneapi.PeerEntry) error {
		params := &dataplaneapi.ReplacePeerEntryParams{
			TransactionId: &txID,
			PeerSection:   peerSectionName,
		}
		clientset := c.Clientset()

		resp, err := client.DispatchUpdate(ctx, c, childName, model,
			func(name string, m v32.PeerEntry, _ *v32.ReplacePeerEntryParams) (*http.Response, error) {
				return clientset.V32().ReplacePeerEntry(ctx, name, (*v32.ReplacePeerEntryParams)(params), m)
			},
			func(name string, m v31.PeerEntry, _ *v31.ReplacePeerEntryParams) (*http.Response, error) {
				return clientset.V31().ReplacePeerEntry(ctx, name, (*v31.ReplacePeerEntryParams)(params), m)
			},
			func(name string, m v30.PeerEntry, _ *v30.ReplacePeerEntryParams) (*http.Response, error) {
				return clientset.V30().ReplacePeerEntry(ctx, name, (*v30.ReplacePeerEntryParams)(params), m)
			},
			(*v32.ReplacePeerEntryParams)(params),
			(*v31.ReplacePeerEntryParams)(params),
			(*v30.ReplacePeerEntryParams)(params),
		)
		if err != nil {
			return err
		}
		defer resp.Body.Close()
		return client.CheckResponse(resp, "peer entry update")
	}
}

// PeerEntryDelete returns an executor for deleting peer entries from peers sections.
func PeerEntryDelete(peerSectionName string) func(ctx context.Context, c *client.DataplaneClient, txID string, containerName string, childName string, model *dataplaneapi.PeerEntry) error {
	return func(ctx context.Context, c *client.DataplaneClient, txID string, _ string, childName string, _ *dataplaneapi.PeerEntry) error {
		params := &dataplaneapi.DeletePeerEntryParams{
			TransactionId: &txID,
			PeerSection:   peerSectionName,
		}
		clientset := c.Clientset()

		resp, err := client.DispatchDelete(ctx, c, childName,
			func(name string, _ *v32.DeletePeerEntryParams) (*http.Response, error) {
				return clientset.V32().DeletePeerEntry(ctx, name, (*v32.DeletePeerEntryParams)(params))
			},
			func(name string, _ *v31.DeletePeerEntryParams) (*http.Response, error) {
				return clientset.V31().DeletePeerEntry(ctx, name, (*v31.DeletePeerEntryParams)(params))
			},
			func(name string, _ *v30.DeletePeerEntryParams) (*http.Response, error) {
				return clientset.V30().DeletePeerEntry(ctx, name, (*v30.DeletePeerEntryParams)(params))
			},
			(*v32.DeletePeerEntryParams)(params),
			(*v31.DeletePeerEntryParams)(params),
			(*v30.DeletePeerEntryParams)(params),
		)
		if err != nil {
			return err
		}
		defer resp.Body.Close()
		return client.CheckResponse(resp, "peer entry deletion")
	}
}

// =============================================================================
// Nameserver Executors (Resolver container)
// =============================================================================

// NameserverCreate returns an executor for creating nameservers in resolver sections.
func NameserverCreate(resolverName string) func(ctx context.Context, c *client.DataplaneClient, txID string, containerName string, childName string, model *dataplaneapi.Nameserver) error {
	return func(ctx context.Context, c *client.DataplaneClient, txID string, _ string, _ string, model *dataplaneapi.Nameserver) error {
		params := &dataplaneapi.CreateNameserverParams{
			TransactionId: &txID,
			Resolver:      resolverName,
		}
		clientset := c.Clientset()

		resp, err := client.DispatchCreate(ctx, c, model,
			func(m v32.Nameserver, _ *v32.CreateNameserverParams) (*http.Response, error) {
				return clientset.V32().CreateNameserver(ctx, (*v32.CreateNameserverParams)(params), m)
			},
			func(m v31.Nameserver, _ *v31.CreateNameserverParams) (*http.Response, error) {
				return clientset.V31().CreateNameserver(ctx, (*v31.CreateNameserverParams)(params), m)
			},
			func(m v30.Nameserver, _ *v30.CreateNameserverParams) (*http.Response, error) {
				return clientset.V30().CreateNameserver(ctx, (*v30.CreateNameserverParams)(params), m)
			},
			(*v32.CreateNameserverParams)(params),
			(*v31.CreateNameserverParams)(params),
			(*v30.CreateNameserverParams)(params),
		)
		if err != nil {
			return err
		}
		defer resp.Body.Close()
		return client.CheckResponse(resp, "nameserver creation")
	}
}

// NameserverUpdate returns an executor for updating nameservers in resolver sections.
func NameserverUpdate(resolverName string) func(ctx context.Context, c *client.DataplaneClient, txID string, containerName string, childName string, model *dataplaneapi.Nameserver) error {
	return func(ctx context.Context, c *client.DataplaneClient, txID string, _ string, childName string, model *dataplaneapi.Nameserver) error {
		params := &dataplaneapi.ReplaceNameserverParams{
			TransactionId: &txID,
			Resolver:      resolverName,
		}
		clientset := c.Clientset()

		resp, err := client.DispatchUpdate(ctx, c, childName, model,
			func(name string, m v32.Nameserver, _ *v32.ReplaceNameserverParams) (*http.Response, error) {
				return clientset.V32().ReplaceNameserver(ctx, name, (*v32.ReplaceNameserverParams)(params), m)
			},
			func(name string, m v31.Nameserver, _ *v31.ReplaceNameserverParams) (*http.Response, error) {
				return clientset.V31().ReplaceNameserver(ctx, name, (*v31.ReplaceNameserverParams)(params), m)
			},
			func(name string, m v30.Nameserver, _ *v30.ReplaceNameserverParams) (*http.Response, error) {
				return clientset.V30().ReplaceNameserver(ctx, name, (*v30.ReplaceNameserverParams)(params), m)
			},
			(*v32.ReplaceNameserverParams)(params),
			(*v31.ReplaceNameserverParams)(params),
			(*v30.ReplaceNameserverParams)(params),
		)
		if err != nil {
			return err
		}
		defer resp.Body.Close()
		return client.CheckResponse(resp, "nameserver update")
	}
}

// NameserverDelete returns an executor for deleting nameservers from resolver sections.
func NameserverDelete(resolverName string) func(ctx context.Context, c *client.DataplaneClient, txID string, containerName string, childName string, model *dataplaneapi.Nameserver) error {
	return func(ctx context.Context, c *client.DataplaneClient, txID string, _ string, childName string, _ *dataplaneapi.Nameserver) error {
		params := &dataplaneapi.DeleteNameserverParams{
			TransactionId: &txID,
			Resolver:      resolverName,
		}
		clientset := c.Clientset()

		resp, err := client.DispatchDelete(ctx, c, childName,
			func(name string, _ *v32.DeleteNameserverParams) (*http.Response, error) {
				return clientset.V32().DeleteNameserver(ctx, name, (*v32.DeleteNameserverParams)(params))
			},
			func(name string, _ *v31.DeleteNameserverParams) (*http.Response, error) {
				return clientset.V31().DeleteNameserver(ctx, name, (*v31.DeleteNameserverParams)(params))
			},
			func(name string, _ *v30.DeleteNameserverParams) (*http.Response, error) {
				return clientset.V30().DeleteNameserver(ctx, name, (*v30.DeleteNameserverParams)(params))
			},
			(*v32.DeleteNameserverParams)(params),
			(*v31.DeleteNameserverParams)(params),
			(*v30.DeleteNameserverParams)(params),
		)
		if err != nil {
			return err
		}
		defer resp.Body.Close()
		return client.CheckResponse(resp, "nameserver deletion")
	}
}
