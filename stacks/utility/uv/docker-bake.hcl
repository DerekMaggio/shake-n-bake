
target "all" {
    name = "build-${item.image_name}"
    description = "Build python script runner for ${item.image_name}"
    dockerfile = "Dockerfile"
    context = "cwd://."
    matrix = {
        item = [
            {
                image_name = "version-bump",
                file_path = "/scripts/version_bump.py",
            }
        ]
    }
    args = {
        SCRIPT_FILE = "${item.file_path}",
    }
    tags = [
        get_full_image_tag("utility", item.image_name, "latest", "${CI}"),
    ]
}