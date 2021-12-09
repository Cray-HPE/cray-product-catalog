👋  Hey! Here is the image we built for you:

```{{ .fullImageWithShaTag }}```

You can use this script to pull the image from the build server to a dev system.
Good luck and make rocket go now! 🌮 🚀

```
#!/usr/bin/env bash

export FULL_IMAGE_WITH_TAG={{ .fullImageWithShaTag }}
export IMAGE_WITH_TAG={{ .imageWithShaTag }}
export SLES_SP=SP2
cat << EOF > /etc/zypp/repos.d/SUSE-SLE-Module-Server-Applications-15-${SLES_SP}-x86_64-Product.repo
[SLE-Module-Server-Applications-15-${SLES_SP}-x86_64-Updates]
enabled=1
autorefresh=0
baseurl=https://slemaster.us.cray.com/SUSE/Products/SLE-Module-Server-Applications/15-${SLES_SP}/x86_64/product
EOF

zypper refresh
zypper in -y --repo SLE-Module-Server-Applications-15-${SLES_SP}-x86_64-Updates skopeo
skopeo copy --dest-tls-verify=false docker://${FULL_IMAGE_WITH_TAG} docker://registry.local/cray/${IMAGE_WITH_TAG}
zypper rr SLE-Module-Server-Applications-15-${SLES_SP}-x86_64-Updates
```