function "get_target_name" {
    params = [item]
    result = contains(keys(item), "dockerfile_tgt") ? item.dockerfile_tgt : item.bake_tgt
}

function "get_image_name" {
    params = [item]
    result = contains(keys(item), "image_name") ? item.image_name : item.bake_tgt
}

function get_node_version {
    params = [item]
    result = equal(item.bake_tgt, "wf_node") ? "${WF_NODE_VERSION}" : "${NODE_VERSION}"
}

target "all" {
    name = "build-${item.bake_tgt}"
    inherits = ["_versions", "_user"]
    description = "Builds the base ${get_image_name(item)} image."
    dockerfile = "Dockerfile"
    matrix = {
        item = [
            {
                bake_tgt = "ubuntu",
                dockerfile_tgt = "ubuntu-base",
                tag = "${UBUNTU_VERSION}"
            },
            {
                bake_tgt = "jdk",
                tag = "${JAVA_VERSION}"
            },
            {
                bake_tgt = "jre",
                tag = "${JAVA_VERSION}"
            },
            {
                bake_tgt = "node",
                tag = "${NODE_VERSION}"
            },
            {
                bake_tgt = "wf_node",
                dockerfile_tgt = "node", 
                image_name = "node",
                tag = "${WF_NODE_VERSION}"
            },
            {
                bake_tgt = "node_jdk",
                image_name = "node-jdk",
                tag = "${NODE_VERSION}-${JAVA_VERSION}"
            },
            {
                bake_tgt = "tomcat",
                tag = "${TOMCAT_VERSION}"
            },
            {
                bake_tgt = "mongo",
                tag = "${MONGO_VERSION}"
            }
        ]
    }
    target = "${get_target_name(item)}"
    args = {
        NODE_VERSION = "${get_node_version(item)}"
    }
    tags = [
        get_full_image_tag("base", get_image_name(item), item.tag, false),
        get_full_image_tag("base", get_image_name(item), "${item.tag}-${datetime}", "${CI}")
    ]
}