FROM alpine:3.20

RUN apk add --no-cache curl bash

COPY scripts/init-gitlab.sh /init-gitlab.sh
RUN chmod +x /init-gitlab.sh

ENTRYPOINT ["/bin/bash", "/init-gitlab.sh"]
