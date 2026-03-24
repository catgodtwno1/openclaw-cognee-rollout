#!/usr/bin/env python3
from pathlib import Path

PLUGIN = Path.home() / '.openclaw' / 'extensions' / 'cognee-openclaw' / 'dist' / 'src' / 'sync.js'
old = '''                catch (updateError) {
                    const errorMsg = updateError instanceof Error ? updateError.message : String(updateError);
                    if (errorMsg.includes("404") || errorMsg.includes("409") || errorMsg.includes("not found")) {
                        logger.info?.(`cognee-openclaw: update failed for ${file.path}, falling back to add`);
                        delete existing.dataId;
                    }
                    else {
                        throw updateError;
                    }
                }
            }
            const response = await client.add({ data: dataWithMetadata, datasetName: dsName, datasetId });
'''
new = '''                catch (updateError) {
                    const errorMsg = updateError instanceof Error ? updateError.message : String(updateError);
                    if (errorMsg.includes("404") || errorMsg.includes("409") || errorMsg.includes("not found")) {
                        logger.info?.(`cognee-openclaw: update failed for ${file.path}, replacing via add+delete`);
                        const oldDataId = existing.dataId;
                        const response = await client.add({ data: dataWithMetadata, datasetName: dsName, datasetId });
                        if (response.datasetId && response.datasetId !== datasetId) {
                            datasetId = response.datasetId;
                            const state = await loadDatasetState();
                            state[dsName] = response.datasetId;
                            await saveDatasetState(state);
                        }
                        syncIndex.entries[file.path] = { hash: file.hash, dataId: response.dataId };
                        syncIndex.datasetId = datasetId;
                        syncIndex.datasetName = dsName;
                        needsCognify = true;
                        result.updated++;
                        logger.info?.(`cognee-openclaw: replaced ${file.path}`);
                        if (oldDataId && oldDataId !== response.dataId && datasetId) {
                            const deleteResult = await client.delete({ dataId: oldDataId, datasetId, mode: cfg.deleteMode });
                            if (!deleteResult.deleted && deleteResult.error) {
                                const isNotFound = deleteResult.error.includes("404") || deleteResult.error.includes("409") || deleteResult.error.includes("not found");
                                if (!isNotFound) {
                                    logger.warn?.(`cognee-openclaw: replacement cleanup failed for ${file.path}: ${deleteResult.error}`);
                                }
                            }
                        }
                        continue;
                    }
                    else {
                        throw updateError;
                    }
                }
            }
            const response = await client.add({ data: dataWithMetadata, datasetName: dsName, datasetId });
'''

if not PLUGIN.exists():
    raise SystemExit(f'Plugin file not found: {PLUGIN}')
text = PLUGIN.read_text()
if new in text:
    print('Already patched:', PLUGIN)
    raise SystemExit(0)
if old not in text:
    raise SystemExit('Target snippet not found; inspect plugin version before patching')
PLUGIN.write_text(text.replace(old, new))
print('Patched:', PLUGIN)
