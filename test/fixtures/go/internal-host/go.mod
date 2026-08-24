// A dependency on an internal module host. Go fetches by module path, so no
// external consumer can ever resolve this — the gate must fail closed.
module github.com/twilio/sdk-actions

go 1.21

require (
	code.hq.twilio.com/core/telemetry v0.4.2
	github.com/stretchr/testify v1.9.0
)
