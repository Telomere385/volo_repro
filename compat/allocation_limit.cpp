// Local per-process workaround for Isaac Sim 5.x on NVIDIA R595.
// Only clamp UINT64_MAX maxMemoryAllocationSize; preserve all other properties.
// Uses the standard Vulkan layer loader chain; never replaces NVIDIA libraries.
#include <vulkan/vulkan.h>
#include <vulkan/vk_layer.h>
#include <cstring>
#include <mutex>
#include <unordered_map>
#include <cstdint>

struct InstanceDispatch {
    VkInstance instance;
    PFN_vkGetInstanceProcAddr gipa;
    PFN_vkGetPhysicalDeviceProperties2 props2;
    PFN_vkGetPhysicalDeviceProperties2KHR props2khr;
    PFN_vkGetPhysicalDeviceProperties props;
    PFN_vkDestroyInstance destroy;
};
struct DeviceDispatch { PFN_vkGetDeviceProcAddr gdpa; PFN_vkDestroyDevice destroy; };
static std::mutex mu;
static std::unordered_map<void*, InstanceDispatch> instances;
static std::unordered_map<void*, DeviceDispatch> devices;
template<class T> static void* key(T h) { return *reinterpret_cast<void**>(h); }
static InstanceDispatch get(VkInstance h) {
    std::lock_guard<std::mutex> lock(mu); return instances.at(key(h));
}
static InstanceDispatch get(VkPhysicalDevice h) {
    std::lock_guard<std::mutex> lock(mu); return instances.at(key(h));
}
extern "C" {
VKAPI_ATTR PFN_vkVoidFunction VKAPI_CALL vkGetInstanceProcAddr(VkInstance, const char*);
VKAPI_ATTR PFN_vkVoidFunction VKAPI_CALL vkGetDeviceProcAddr(VkDevice, const char*);
VKAPI_ATTR VkResult VKAPI_CALL vkCreateInstance(const VkInstanceCreateInfo* info,
        const VkAllocationCallbacks* alloc, VkInstance* result) {
    auto chain = reinterpret_cast<VkLayerInstanceCreateInfo*>(const_cast<void*>(info->pNext));
    while (chain && !(chain->sType == VK_STRUCTURE_TYPE_LOADER_INSTANCE_CREATE_INFO &&
                       chain->function == VK_LAYER_LINK_INFO))
        chain = reinterpret_cast<VkLayerInstanceCreateInfo*>(const_cast<void*>(chain->pNext));
    if (!chain) return VK_ERROR_INITIALIZATION_FAILED;
    auto gipa = chain->u.pLayerInfo->pfnNextGetInstanceProcAddr;
    auto create = reinterpret_cast<PFN_vkCreateInstance>(gipa(VK_NULL_HANDLE, "vkCreateInstance"));
    chain->u.pLayerInfo = chain->u.pLayerInfo->pNext;
    auto r = create(info, alloc, result);
    if (r != VK_SUCCESS) return r;
    InstanceDispatch d{*result, gipa,
      reinterpret_cast<PFN_vkGetPhysicalDeviceProperties2>(gipa(*result,"vkGetPhysicalDeviceProperties2")),
      reinterpret_cast<PFN_vkGetPhysicalDeviceProperties2KHR>(gipa(*result,"vkGetPhysicalDeviceProperties2KHR")),
      reinterpret_cast<PFN_vkGetPhysicalDeviceProperties>(gipa(*result,"vkGetPhysicalDeviceProperties")),
      reinterpret_cast<PFN_vkDestroyInstance>(gipa(*result,"vkDestroyInstance"))};
    std::lock_guard<std::mutex> lock(mu); instances[key(*result)] = d;
    return r;
}
VKAPI_ATTR void VKAPI_CALL vkDestroyInstance(VkInstance h, const VkAllocationCallbacks* a) {
    auto d=get(h);
    { std::lock_guard<std::mutex> lock(mu); instances.erase(key(h)); }
    d.destroy(h,a);
}
static void clamp(VkPhysicalDeviceProperties2* p) {
    if (p->properties.vendorID != 0x10de) return;
    for (auto n=reinterpret_cast<VkBaseOutStructure*>(p->pNext); n; n=n->pNext) {
        VkDeviceSize* limit=nullptr;
        if (n->sType==VK_STRUCTURE_TYPE_PHYSICAL_DEVICE_MAINTENANCE_3_PROPERTIES)
            limit=&reinterpret_cast<VkPhysicalDeviceMaintenance3Properties*>(n)->maxMemoryAllocationSize;
        if (n->sType==VK_STRUCTURE_TYPE_PHYSICAL_DEVICE_VULKAN_1_1_PROPERTIES)
            limit=&reinterpret_cast<VkPhysicalDeviceVulkan11Properties*>(n)->maxMemoryAllocationSize;
        if (limit && *limit==UINT64_MAX) *limit=UINT64_C(4292870144);
    }
}
VKAPI_ATTR void VKAPI_CALL vkGetPhysicalDeviceProperties2(VkPhysicalDevice h, VkPhysicalDeviceProperties2* p) {
    auto d=get(h);
    (d.props2 ? d.props2 : d.props2khr)(h,p);
    clamp(p);
}
VKAPI_ATTR void VKAPI_CALL vkGetPhysicalDeviceProperties2KHR(VkPhysicalDevice h, VkPhysicalDeviceProperties2* p) {
    auto d=get(h);
    (d.props2khr ? d.props2khr : d.props2)(h,p);
    clamp(p);
}
VKAPI_ATTR VkResult VKAPI_CALL vkCreateDevice(VkPhysicalDevice h, const VkDeviceCreateInfo* info,
        const VkAllocationCallbacks* alloc, VkDevice* result) {
    auto chain=reinterpret_cast<VkLayerDeviceCreateInfo*>(const_cast<void*>(info->pNext));
    while (chain && !(chain->sType==VK_STRUCTURE_TYPE_LOADER_DEVICE_CREATE_INFO &&
                       chain->function==VK_LAYER_LINK_INFO))
        chain=reinterpret_cast<VkLayerDeviceCreateInfo*>(const_cast<void*>(chain->pNext));
    if (!chain) return VK_ERROR_INITIALIZATION_FAILED;
    auto gipa=chain->u.pLayerInfo->pfnNextGetInstanceProcAddr;
    auto gdpa=chain->u.pLayerInfo->pfnNextGetDeviceProcAddr;
    auto d=get(h);
    auto create=reinterpret_cast<PFN_vkCreateDevice>(gipa(d.instance,"vkCreateDevice"));
    chain->u.pLayerInfo=chain->u.pLayerInfo->pNext;
    auto r=create(h,info,alloc,result);
    if (r!=VK_SUCCESS) return r;
    std::lock_guard<std::mutex> lock(mu);
    devices[key(*result)]={gdpa,reinterpret_cast<PFN_vkDestroyDevice>(gdpa(*result,"vkDestroyDevice"))};
    return r;
}
VKAPI_ATTR void VKAPI_CALL vkDestroyDevice(VkDevice h,const VkAllocationCallbacks* a) {
    DeviceDispatch d;
    { std::lock_guard<std::mutex> lock(mu); d=devices.at(key(h)); devices.erase(key(h)); }
    d.destroy(h,a);
}
VKAPI_ATTR PFN_vkVoidFunction VKAPI_CALL vkGetDeviceProcAddr(VkDevice h,const char* name) {
    if (!std::strcmp(name,"vkGetDeviceProcAddr")) return reinterpret_cast<PFN_vkVoidFunction>(vkGetDeviceProcAddr);
    if (!std::strcmp(name,"vkDestroyDevice")) return reinterpret_cast<PFN_vkVoidFunction>(vkDestroyDevice);
    PFN_vkGetDeviceProcAddr next;
    { std::lock_guard<std::mutex> lock(mu); next=devices.at(key(h)).gdpa; }
    return next(h,name);
}
VKAPI_ATTR PFN_vkVoidFunction VKAPI_CALL vkGetInstanceProcAddr(VkInstance h,const char* name) {
#define ENTRY(f) if (!std::strcmp(name,#f)) return reinterpret_cast<PFN_vkVoidFunction>(f)
    ENTRY(vkGetInstanceProcAddr); ENTRY(vkGetDeviceProcAddr);
    ENTRY(vkCreateInstance); ENTRY(vkDestroyInstance);
    ENTRY(vkCreateDevice); ENTRY(vkDestroyDevice);
    ENTRY(vkGetPhysicalDeviceProperties2); ENTRY(vkGetPhysicalDeviceProperties2KHR);
#undef ENTRY
    return h ? get(h).gipa(h,name) : nullptr;
}
VKAPI_ATTR VkResult VKAPI_CALL vkNegotiateLoaderLayerInterfaceVersion(VkNegotiateLayerInterface* v) {
    if (v->loaderLayerInterfaceVersion<2) return VK_ERROR_INITIALIZATION_FAILED;
    v->loaderLayerInterfaceVersion=2;
    v->pfnGetInstanceProcAddr=vkGetInstanceProcAddr;
    v->pfnGetDeviceProcAddr=vkGetDeviceProcAddr;
    v->pfnGetPhysicalDeviceProcAddr=nullptr;
    return VK_SUCCESS;
}
}
