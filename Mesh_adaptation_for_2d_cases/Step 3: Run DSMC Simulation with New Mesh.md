## Run DSMC Simulation with the New Mesh

- **Replace the old mesh** with the newly generated refined mesh.
- **Run the DSMC simulation again** on the refined mesh.
- **Plot the cell size to mean free path ratio** to verify mesh accuracy:
  - If each cell size is approximately equal to the local mean free path, the plot will appear almost linear.
  - If not, repeat the refinement process.
- Once a well-refined mesh is confirmed, you can proceed to extract improved results for variables such as pressure, density, temperature, surface heat flux, and other flow properties. These values should demonstrate better accuracy compared to the results from the uniform mesh.

---
