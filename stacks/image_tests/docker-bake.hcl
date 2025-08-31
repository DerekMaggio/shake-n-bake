# Alrighty, so this logic is pretty dense. Let's break it down:
# 1. image_tests (this folder) implicitly depends on the images_under_test.hcl file. See __REQUIRED_BAKE_FILES.json
# 2. The build_matrix function looks at each image configuration, uses identifier to look the the list of tags.
# 3. For each tag, it creates a map with identifier, tests, and tag.
# 4. The result is a flattened list of maps, each representing a specific image configuration with its associated tests and tag.

# Example output of build_matrix:
# Note the multiple node versions, which causes this nightmare of a matrix
# [
#   {
#     "identifier": "base/ubuntu",
#     "tests": ["ubuntu.bats"],
#     "tag": "24.04"
#   },
#   {
#     "identifier": "base/node",
#     "tests": ["ubuntu.bats", "node.bats"],
#     "tag": "18.20.5"
#   }, 
#   {
#     "identifier": "base/node",
#     "tests": ["ubuntu.bats", "node.bats"],
#     "tag": "20.17.0"
#   },
#   {
#     "identifier": "base/node-jdk",
#     "tests": ["ubuntu.bats", "node.bats"],
#     "tag": "20.17.0-17.0.14"
#   },
#   ...
# ]

variable "image_configs" {
    default = [
        {
            identifier = "base/ubuntu"
            tests = ["ubuntu.bats"]
        },
        {
            identifier = "devcontainers/huloop-dev-tools"
            tests = ["ubuntu.bats", "huloop_dev_tools.bats"]
        },
        {
            identifier = "base/jdk"
            tests = ["ubuntu.bats", "jdk.bats"]
        },
        {
            identifier = "base/jre"
            tests = ["ubuntu.bats", "jre.bats"]
        },
        {
            identifier = "base/node"
            tests = ["ubuntu.bats", "node.bats"]
        },
        {
            identifier = "base/tomcat"
            tests = ["ubuntu.bats", "jre.bats", "tomcat.bats"]
        },
        {
            identifier = "base/mongo"
            tests = ["ubuntu.bats", "mongo.bats"]
        }
    ]
}

function "build_matrix" {
    params = [images]
    result = flatten([
        for config in image_configs: [
            for match in find_image_tags(
                    images,
                    "(^|/)${config.identifier}$",
                    ".*"
                ): {
                identifier = match.image_name
                tests = config.tests
                tag = match.tag
            }
        ]
    ])
}

target "all" {
    name = regex_replace("test_${item.identifier}_${item.tag}", "[^a-zA-Z0-9]", "_")
    inherits = ["_user", "_versions"]
    description = "Shared settings for all targets."
    dockerfile = "Dockerfile"
    no-cache-filter = ["test"]
    output = [ { "type" = "cacheonly" } ]
    target = "test"
    args = {
        IMAGE_UNDER_TEST = "${item.identifier}:${item.tag}",
        TEST_FILES = "${join(" ", item.tests)}",
    }
    matrix = { item = build_matrix(_images) }
    
}