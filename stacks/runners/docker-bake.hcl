variable "DOWNLOAD_URL" {
  default = "$DOWNLOAD_URL"
}
variable "PREFIX" {
  default = "$PREFIX"
}

target "_common" {
  args = {
    UBUNTU_BASE_IMAGE = find_image_tags(
        _images,
        "base/ubuntu",
        major_version_regex("24")
    )[0].full_tag

    JDK_BASE_IMAGE = find_image_tags(
        _images,
        "base/jdk",
        major_version_regex("17")
    )[0].full_tag

    JRE_BASE_IMAGE = find_image_tags(
        _images,
        "base/jre",
        major_version_regex("17")
    )[0].full_tag
    DOWNLOAD_URL = "${DOWNLOAD_URL}"
    }
}


target "workflow" {
    inherits = ["_common"]
    target = "spring-boot-layered-runner"
    args = {
        JAR_FILTER = "huloop-workflow*.jar"
    }
    tags = [
        "ghcr.io/agreeya-huloop/runners/workflow-service:${datetime}",
        "ghcr.io/agreeya-huloop/runners/workflow-service:${PREFIX}-${datetime}",
    ]
}

target "okta" {
    inherits = ["_common"]
    target = "spring-boot-runner"
    args = {
        JAR_FILTER = "huloop-sso*.jar"
    }
    tags = [
        "ghcr.io/agreeya-huloop/runners/okta-service:${datetime}",
        "ghcr.io/agreeya-huloop/runners/okta-service:${PREFIX}-${datetime}",
    ]
}

target "reporting" {
    inherits = ["_common"]
    target = "spring-boot-layered-runner"
    args = {
        JAR_FILTER = "huloop-report*.jar"
    }
    tags = [
        "ghcr.io/agreeya-huloop/runners/report-service:${datetime}",
        "ghcr.io/agreeya-huloop/runners/report-service:${PREFIX}-${datetime}",
    ]
}

target "entra-sso-portal"  {
    inherits = ["_common"]
    target = "spring-boot-runner"
    args = {
        JAR_FILTER = "**/security-saml-portal*.jar"
    }
    tags = [
        "ghcr.io/agreeya-huloop/runners/entra-sso-portal:${datetime}",
        "ghcr.io/agreeya-huloop/runners/entra-sso-portal:${PREFIX}-${datetime}",
    ]
}

target "entra-sso-agent" {
    inherits = ["_common"]
    target = "spring-boot-runner"
    args = {
        JAR_FILTER = "**/security-saml-agent*.jar"
    }
    tags = [
        "ghcr.io/agreeya-huloop/runners/entra-sso-agent:${datetime}",
        "ghcr.io/agreeya-huloop/runners/entra-sso-agent:${PREFIX}-${datetime}",
    ]
}

group "all" {
    targets = [
        "workflow",
        "okta",
        "reporting",
        "entra-sso-portal",
        "entra-sso-agent"
    ]
}