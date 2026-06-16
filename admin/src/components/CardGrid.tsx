import { Box, type BoxProps } from "@mui/material";

export const CardGrid = (props: BoxProps) => (
  <Box
    {...props}
    sx={{
      display: "grid",
      gridTemplateColumns: "repeat(auto-fill, minmax(240px, 1fr))",
      gap: 2,
      width: "100%",
      ...(props.sx as object),
    }}
  />
);
