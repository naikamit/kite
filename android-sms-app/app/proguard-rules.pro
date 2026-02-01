# Kite SMS ProGuard Rules

# Keep model classes
-keep class com.kite.sms.model.** { *; }

# Glide
-keep public class * implements com.bumptech.glide.module.GlideModule
-keep class * extends com.bumptech.glide.module.AppGlideModule { <init>(...); }
-keep public enum com.bumptech.glide.load.ImageHeaderParser$** {
  **[] $VALUES;
  public *;
}

# AndroidX
-keep class androidx.** { *; }
-dontwarn androidx.**

# Material
-keep class com.google.android.material.** { *; }
-dontwarn com.google.android.material.**
