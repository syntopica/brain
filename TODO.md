# Open work

- [ ] Coordinate the `x-path-kind` schema annotation with the Clips reader before publishing it. `src/config/validate-syntopica-schema-vocabulary.ts` in syntopica-clips rejects the annotation as `Unsupported configuration schema keyword`; Clips loads this engine's schema. Add the keyword to that validator's allowlist and test the annotated schema. Approval to edit the sibling repository is pending; no instance configuration change is needed.
