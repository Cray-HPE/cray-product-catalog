👋  Hey! Here is the image we built for you ([Artifactory Link](https://artifactory.algol60.net/ui/repos/tree/General/csm-docker%2F{{ .isStable }}%2F{{ .imageName }}%2F{{ .imageTag }})):

```bash
{{ .imageDownloadLink }}
```

Use podman or docker to pull it down and inspect locally:

```bash
podman pull {{ .imageDownloadLink }}
```

Or, use this script to pull the image from the build server to a dev system:

<details>
<summary>Dev System Pull Script</summary>
<br />

```
#!/usr/bin/env bash

export REMOTE_IMAGE={{ .fullImage }}
export LOCAL_IMAGE={{ .imageName }}:{{ .imageTag }}

zypper addrepo https://slemaster.us.cray.com/SUSE/Products/SLE-Module-Server-Applications/15-SP2/x86_64/product {{ .zypperRepoName }}
zypper refresh
zypper in -y --repo {{ .zypperRepoName }} skopeo
skopeo copy --dest-tls-verify=false docker://${REMOTE_IMAGE} docker://registry.local/cray/${LOCAL_IMAGE}
zypper rr {{ .zypperRepoName }}
```
</details>

*Note*: this SHA is the merge of {{ .PRHeadSha }} and the PR base branch. Make rocket go now! 🌮 🚀