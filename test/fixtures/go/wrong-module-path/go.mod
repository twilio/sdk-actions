// Module path does not match the repo it is published from, so `go get` on the
// declared path resolves to something else entirely (or to nothing).
module github.com/some-other-org/not-this-repo

go 1.21

require github.com/stretchr/testify v1.9.0
