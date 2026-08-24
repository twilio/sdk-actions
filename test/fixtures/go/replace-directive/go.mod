// A `replace` directive. The go command honours replace only in the MAIN
// module, so CI resolves the fork while every consumer resolves upstream.
module github.com/twilio/sdk-actions

go 1.21

require github.com/stretchr/testify v1.9.0

replace github.com/stretchr/testify => github.com/twilio-internal/testify-fork v1.9.1
