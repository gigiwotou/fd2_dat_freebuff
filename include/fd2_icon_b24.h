#ifndef FD2_ICON_B24_H
#define FD2_ICON_B24_H

/*
 * fd2_icon_b24.h - FDICON.B24 icon loader for FD2
 * 
 * Based on IDA analysis of sub_11019 (0x11019)
 * 
 * FDICON.B24 contains map event icons/sprites. Each icon has 12 segments
 * (possibly 12 directions or animation frames). The loader caches icons
 * in a shared buffer with offset adjustment.
 */

#ifdef __cplusplus
extern "C" {
#endif

/**
 * Initialize the FDICON.B24 system
 * 
 * Reads the offset table and allocates the main icon buffer.
 * Should be called once during game initialization.
 * 
 * @param fdicon_path Path to FDICON.B24 file
 * @return 0 on success, -1 on error
 */
int fd2_icon_init(const char* fdicon_path);

/**
 * Load an icon into cache and return its cache index
 * 
 * Based on IDA sub_11019(int icon_id, FILE* fd):
 * - Checks if icon is already cached (by ID)
 * - If not, reads icon data from file into shared buffer
 * - Stores adjusted offsets for 12 segments
 * - Returns cache index
 * 
 * @param icon_id Icon index to load (0-139)
 * @return Cache index on success, -1 on error
 */
int fd2_icon_get(int icon_id);

/**
 * Get pointer to icon data for a specific segment
 * 
 * Each icon has 12 segments. The offsets are stored in the
 * buffer header area and adjusted to absolute positions.
 * 
 * @param cache_index Index returned by fd2_icon_get
 * @param segment Segment index (0-11)
 * @return Pointer to segment data, or NULL if invalid
 */
unsigned char* fd2_icon_get_segment(int cache_index, int segment);

/**
 * Get the main icon buffer pointer
 * 
 * Returns the raw buffer pointer (matching game's dword_53A61).
 * Use fd2_icon_get_segment() for easier access.
 * 
 * @return Pointer to start of icon buffer, or NULL if not initialized
 */
unsigned char* fd2_icon_get_buffer(void);

/**
 * Get current buffer usage in bytes
 * 
 * @return Number of bytes used in buffer
 */
int fd2_icon_get_buffer_size(void);

/**
 * Get number of icons currently in cache
 * 
 * @return Number of cached icons
 */
int fd2_icon_get_cached_count(void);

/**
 * Get total icon count from file
 * 
 * @return Total number of icons in FDICON.B24
 */
int fd2_icon_get_count(void);

/**
 * Get the cached icon ID for a given cache index
 * 
 * @param cache_index Cache index (0 to cached_count-1)
 * @return Icon ID, or -1 if invalid
 */
int fd2_icon_get_cached_id(int cache_index);

/**
 * Cleanup and free all resources
 * 
 * Closes the file, frees buffers, and resets state.
 */
void fd2_icon_shutdown(void);

#ifdef __cplusplus
}
#endif

#endif /* FD2_ICON_B24_H */
