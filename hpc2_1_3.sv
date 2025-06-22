(* keep_hierarchy="true", dont_touch="true" *)
module hpc2_1_3 #(
    parameter NUM_SHARES = 2
) (
    (* SILVER="clock" *) input clock,
    (* SILVER="0_[1:0]" *) input logic [NUM_SHARES-1:0] a,
    (* SILVER="1_[1:0]" *) input logic [NUM_SHARES-1:0] b,
    (* SILVER="2_[1:0]" *) input logic [NUM_SHARES-1:0] c,
    (* SILVER="refresh" *) input logic [2:0] r,
    (* SILVER="3_[1:0]" *) output logic [NUM_SHARES-1:0] p
);
  (* keep="true", dont_touch="true" *) logic [NUM_SHARES:0] t[4], tt, c_r, b_r, bc_r, bb, cc;
  (* keep="true", dont_touch="true" *) logic rr;

  always_ff @(posedge clock) begin
    rr <= ^r;
    bb <= b;
    cc <= c;
    for (int i = 0; i < NUM_SHARES; i++) begin
      tt[i]  <= (b[i] & c[i]) ^ (b[i] & r[0]) ^ (c[i] & r[1]) ^ r[2];
      t[0][i] <= (a[i] & tt[i]) ^ rr;
      for (int j = 0; j < NUM_SHARES; j++) begin
        if (j != i) begin
          c_r[i]  <= c[j] ^ r[0];
          b_r[i]  <= b[j] ^ r[1];
          bc_r[i] <= (b[j] & c[j]) ^ r[2];
        end
      end
      t[1][i] <= a[i] & c_r[i] & bb[i];
      t[2][i] <= a[i] & b_r[i] & cc[i];
      t[3][i] <= a[i] & bc_r[i];
    end
  end

  assign p = t[0] ^ t[1] ^ t[2] ^ t[3];

`ifndef SYNTHESIS
`ifdef FORMAL
  logic [1:0] counter = 0;
  always @(posedge clock) begin
    if (counter == 2) begin
      assert__1 : assert (^p == $past((^a) & $past((^b) & (^c))));
    end else begin
      counter <= counter + 1;
    end
  end
`endif
`endif

endmodule
