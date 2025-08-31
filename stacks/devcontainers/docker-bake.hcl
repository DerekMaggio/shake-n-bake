target "_shared" {
    inherits = ["_user", "_versions"]
    description = "Shared settings for all targets."
    dockerfile = "Dockerfile"
    contexts = {
        docker-folder = "cwd://../"
        huloop-dev-tools = "cwd://huloop-dev-tools/"
    }
}

function "get_target_name" {
    params = [item]
    result = item.bake_tgt
}

function "get_image_name" {
    params = [item]
    result = contains(keys(item), "image_name") ? item.image_name : item.bake_tgt
}

target "all" {
    name = "build-${item.bake_tgt}"
    inherits = ["_shared"]
    description = "Builds the devcontainer ${get_image_name(item)} image."
    matrix = {
        item = [
            {
                bake_tgt = "huloop_dev_tools"
                image_name = "huloop-dev-tools"
                dockerfile_target = "huloop-dev-tools-deps"
                dev_container_source = "base/ubuntu:${UBUNTU_VERSION}"
            },
            {
                bake_tgt = "huloop_v5"
                image_name = "huloop-v5"
                dockerfile_target = "huloop-v5-deps"
                dev_container_source = "base/node-jdk:${NODE_VERSION}-${JAVA_VERSION}"
            },
            {
                bake_tgt = "azure_sso"
                image_name = "azure-sso"
                dockerfile_target = "azure-sso-deps"
                dev_container_source = "base/jdk:${JAVA_VERSION}"
            },
            {
                bake_tgt = "workflow_ui"
                image_name = "workflow-ui"
                dockerfile_target = "workflow-ui-deps"
                dev_container_source = "base/node:${WF_NODE_VERSION}"
            }
        ]
    }
    target = "${item.dockerfile_target}"
    args = {
        DEV_CONTAINER_SOURCE = "${item.dev_container_source}"
    }
    tags = [
        get_full_image_tag("devcontainers", get_image_name(item), "temp", false),
        get_full_image_tag("devcontainers", get_image_name(item), "${datetime}", "${CI}")
    ]
}