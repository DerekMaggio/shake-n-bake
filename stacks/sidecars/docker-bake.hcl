

target "_common" {
  args = {
    JDK_BASE_IMAGE = find_image_tags(
        _images,
        "base/jdk",
        major_version_regex("17")
    )[0].full_tag
    }
}


target "keystore-builder" {
    inherits = ["_common", "_user"]
    target = "keystore-builder"
    context = "cwd://entra_sso_keystore_builder"
    tags = [
        "ghcr.io/agreeya-huloop/sidecars/keystore-builder:${datetime}",
    ]
}


group "all" {
    targets = [
        "keystore-builder"
    ]
}