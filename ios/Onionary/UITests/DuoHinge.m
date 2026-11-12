// Simulator test support only. Uses the Device Hub event format also documented
// by Appium's XCUIDevice+FBHinge. Run in XCTest's existing simulator context:
// no extra simctl process, bootstrap session, HTTP server or startup handshake.
#import "OnionaryUITests-Bridging-Header.h"
#import <TargetConditionals.h>
#import <dlfcn.h>
#import <mach/mach_time.h>
#import <math.h>

NSInteger OnionarySetHingeAngle(double angle) {
    if (!isfinite(angle) || angle < 0 || angle > 180) return 1;
#if !TARGET_OS_SIMULATOR
    return 2;
#else
    if (![NSThread isMainThread]) return 3;
    static CFDataRef (*serialize)(CFTypeRef, CFOptionFlags);
    static CFTypeRef (*createEvent)(CFAllocatorRef, uint64_t, uint32_t, uint32_t, uint32_t, uint8_t *, CFIndex, uint32_t);
    static void (*dispatchEvent)(CFTypeRef, CFTypeRef);
    static CFTypeRef client;
    static dispatch_once_t once;
    dispatch_once(&once, ^{
        void *library = dlopen("/System/Library/Frameworks/IOKit.framework/IOKit", RTLD_LAZY);
        if (!library) return;
        serialize = dlsym(library, "IOCFSerialize");
        createEvent = dlsym(library, "IOHIDEventCreateVendorDefinedEvent");
        CFTypeRef (*createClient)(CFAllocatorRef) = dlsym(library, "IOHIDEventSystemClientCreate");
        dispatchEvent = dlsym(library, "IOHIDEventSystemClientDispatchEvent");
        if (serialize && createEvent && createClient && dispatchEvent) client = createClient(kCFAllocatorDefault);
    });
    // Failed initialization is terminal for this runner; never retry injection.
    if (!serialize || !createEvent || !dispatchEvent || !client) return 4;
    NSDictionary *payload = @{ @"provider": @"com.apple.Virtualization.VirtualMachines",
                              @"source": @"hinge-slider-control", @"type": @"range", @"value": @(angle) };
    CFDataRef data = serialize((__bridge CFTypeRef)payload, 1);
    if (!data) return 5;
    CFTypeRef event = createEvent(kCFAllocatorDefault, mach_absolute_time(), 0xff61, 0x5b, 0,
                                 (uint8_t *)CFDataGetBytePtr(data), CFDataGetLength(data), 0);
    CFRelease(data);
    if (!event) return 6;
    dispatchEvent(client, event);
    CFRelease(event);
    return 0;
#endif
}
