import * as pulumi from "@pulumi/pulumi";
import * as insights from "@pulumi/azure-native/insights";
import * as resources from "@pulumi/azure-native/resources";
import * as containerregistry from "@pulumi/azure-native/containerregistry";
import * as docker from "@pulumi/docker";
import * as web from "@pulumi/azure-native/web";

const config = new pulumi.Config();
const appPath = config.get("appPath") || "./..";
const imageName = config.get("imageName") || "lab-gen-app";
const imageTag = config.get("imageTag") || "latest";

const resourceGroup = new resources.ResourceGroup("rg-lab-gen");

// Create a container registry.
const registry = new containerregistry.Registry("crlabgen", {
    resourceGroupName: resourceGroup.name,
    adminUserEnabled: true,
    sku: {
        name: containerregistry.SkuName.Basic,
    },
});

// Fetch login credentials for the registry.
const credentials = containerregistry
    .listRegistryCredentialsOutput({
        resourceGroupName: resourceGroup.name,
        registryName: registry.name,
    })
    .apply((creds) => {
        return {
            username: creds.username!,
            password: creds.passwords![0].value!,
        };
    });

const plan = new web.AppServicePlan(`plan-${imageName}`, {
    resourceGroupName: resourceGroup.name,
    kind: "Linux",
    reserved: true,
    sku: {
        name: "B1",
        tier: "Basic",
    },
});

// Create a image for the service.
const image = new docker.Image("image", {
    imageName: pulumi.interpolate`${registry.loginServer}/${imageName}:${imageTag}`,
    build: {
        context: appPath,
        platform: "linux/amd64",
    },
    registry: {
        server: registry.loginServer,
        username: credentials.username,
        password: credentials.password,
    },
});

const appInsights = new insights.Component(`ai-${imageName}`, {
    resourceGroupName: resourceGroup.name,
    kind: "web",
    ingestionMode: "ApplicationInsights",
    applicationType: insights.ApplicationType.Web,
});

const genWebApp = new web.WebApp(`app-${imageName}`, {
    resourceGroupName: resourceGroup.name,
    serverFarmId: plan.id,
    siteConfig: {
        appSettings: [
            {
                name: "WEBSITES_ENABLE_APP_SERVICE_STORAGE",
                value: "false",
            },
            {
                name: "DOCKER_REGISTRY_SERVER_URL",
                value: pulumi.interpolate`https://${registry.loginServer}`,
            },
            {
                name: "DOCKER_REGISTRY_SERVER_USERNAME",
                value: credentials.username,
            },
            {
                name: "DOCKER_REGISTRY_SERVER_PASSWORD",
                value: credentials.password,
            },
            {
                name: "LAB_GEN_PORT",
                value: "80",
            },
            {
                name: "LAB_GEN_HOST",
                value: "0.0.0.0",
            },
            {
                name: "WEBSITES_PORT",
                value: "80",
            },
            {
                name: "APPINSIGHTS_INSTRUMENTATIONKEY",
                value: appInsights.instrumentationKey,
            },
            {
                name: "APPLICATIONINSIGHTS_CONNECTION_STRING",
                value: pulumi.interpolate`InstrumentationKey=${appInsights.instrumentationKey}`,
            },
            {
                name: "ApplicationInsightsAgent_EXTENSION_VERSION",
                value: "~2",
            },
        ],
        alwaysOn: true,
        linuxFxVersion: pulumi.interpolate`DOCKER|${image.imageName}`,
        detailedErrorLoggingEnabled: true,
    },
    httpsOnly: true,
});

export const endpoint = pulumi.interpolate`https://${genWebApp.defaultHostName}`;
