variable "CI" {
    description = "CI environment variable, automatically set to 'true' by GitHub Actions."
    type = string
    default = "false"
}

variable "datetime" {
    description = "Current date and time in RFC3339 format."
    default = "${formatdate("YYYYMMDDmmhhss", timestamp())}"
}

function "get_full_image_tag" {
    params = [prefix, image_name, tag, tag_for_ci]
    result = (
        equal("${tag_for_ci}", "true") ?
        "ghcr.io/agreeya-huloop/${prefix}/${image_name}:${tag}" :
        "${prefix}/${image_name}:${tag}"
    )
}

