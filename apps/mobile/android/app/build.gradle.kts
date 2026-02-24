plugins {
    id("com.android.application")
    id("kotlin-android")
    id("dev.flutter.flutter-gradle-plugin")
}

android {
    namespace = "com.example.mobile" // Ensure this matches your package name
    compileSdk = flutter.compileSdkVersion
    ndkVersion = flutter.ndkVersion

    compileOptions {
        sourceCompatibility = JavaVersion.VERSION_11
        targetCompatibility = JavaVersion.VERSION_11
    }

    kotlinOptions {
        jvmTarget = "11"
    }

    defaultConfig {
        applicationId = "com.example.mobile"
        // Stripe requires minSdk 21
        minSdk = flutter.minSdkVersion 
        targetSdk = flutter.targetSdkVersion
        versionCode = flutter.versionCode
        versionName = flutter.versionName
        
        // This is required for Stripe
        multiDexEnabled = true
    }

    buildTypes {
        release {
            // In Kotlin DSL, use getByName("debug")
            signingConfig = signingConfigs.getByName("debug")
        }
    }
}

dependencies {
    // Note the parentheses for Kotlin DSL
    implementation("androidx.multidex:multidex:2.0.1")
}
