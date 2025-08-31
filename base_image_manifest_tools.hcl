# Example:
# Note that the keys can either be local (e.g., "base/jdk") or remote (e.g., "ghcr.io/agreeya-huloop/base/node"). In practice they will be remote, but we want to allow local testing as well.

# variable "_images" {
#   default = {
#     "base/jdk" = [
#       "17.0.14",
#       "17.0.14-20250617511611"
#     ]
#     "base/jre" = [
#       "17.0.14",
#       "17.0.14-20250617511611"
#     ]
#     "ghcr.io/agreeya-huloop/base/mongo" = [
#       "8.0.5-20250617511611"
#     ]
#     "ghcr.io/agreeya-huloop/base/node" = [
#       "20.17.0-20250617511611",
#       "18.20.5-20250617511611"
#     ]
#     "devcontainers/huloop-v5" = [
#       "temp",
#       "20250617511617"
#     ]
#     "devcontainers/workflow-ui" = [
#       "temp",
#       "20250617511617"
#     ]
#   }
# }


function "find_image_tags" {
    # Find image tags matching a specific regex pattern
    params = [images, image_regex, tag_regex]
    result = flatten([
        for k, v in images: 
            length(regexall(image_regex, k)) > 0 ? 
            [
                for tag in v: {
                    image_name = k
                    tag = tag
                    full_tag = "${k}:${tag}"
                } if can(regex(tag_regex, tag))
            ] : 
            []
    ])
}

function "major_version_regex" {
    # Generate a regex pattern for major version matching
    params = [major_version]
    result = "^${major_version}\\..*-[0-9]{14}"
}