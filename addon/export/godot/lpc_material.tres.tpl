[gd_resource type="ShaderMaterial" load_steps=2 format=3]

[ext_resource type="Shader" path="lpc_shader.gdshader" id="1"]

[resource]
resource_name = "{{name}}"
shader = ExtResource("1")
shader_parameter/emission_factor = {{emission_factor}}
shader_parameter/clearcoat_roughness_value = {{clearcoat_roughness}}
