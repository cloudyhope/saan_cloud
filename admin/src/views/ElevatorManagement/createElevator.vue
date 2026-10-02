<template>
	<div class="follow-order">
		<div class="box">
			<div class="form-container">
				<div class="p-4 m-4">
					<!-- <h5 class="mb-4 text-primary">افزودن آسانسور</h5> -->
					<div>
						<div class="row">
							<div class="col-md-6 mb-3">
								<label class="form-label">عنوان</label>
								<input 
									v-model="formData.title" 
									type="text" 
									class="form-control inputs" 
									required
								/>
							</div>

							<div class="col-md-6 mb-3">
                            <label class="form-label">نوع کاربری:</label>
                            <select v-model="formData.type" class="form-control">
                                <option value="" disabled selected>انتخاب کنید</option>
                                <option value="باری">باری</option>
                                <option value="مسافری">مسافری</option>
                            </select>
                        </div>
							<div class="col-md-6 mb-3">
								<label class="form-label">نوع آسانسور</label>
								<select v-model="formData.elevator_type" class="form-control" required>
									<option value="" disabled>انتخاب کنید</option>
									<option v-for="option in elevatorTypeChoices" :key="option.value" :value="option.value">
										{{ option.label }}
									</option>
								</select>
							</div>

							<div class="col-md-6 mb-3">
								<label class="form-label">نوع استفاده</label>
								<select v-model="formData.usage_type" class="form-control" required>
									<option value="" disabled>انتخاب کنید</option>
									<option v-for="option in usageTypeChoices" :key="option.value" :value="option.value">
										{{ option.label }}
									</option>
								</select>
							</div>

							<div class="col-md-6 mb-3">
								<label class="form-label">ظرفیت کابین (کیلوگرم)</label>
								<input 
									v-model.number="formData.cabin_capacity_kg" 
									type="number" 
									class="form-control inputs" 
									min="0"
									required
								/>
							</div>

							<div class="col-md-6 mb-3">
								<label class="form-label">تعداد ایستگاه‌ها</label>
								<input 
									v-model.number="formData.stops_count" 
									type="number" 
									class="form-control inputs" 
									min="1"
									required
								/>
							</div>

							<div class="col-md-6 mb-3">
								<label class="form-label">نوع عملکرد</label>
								<select v-model="formData.operation_type" class="form-control" required>
									<option value="" disabled>انتخاب کنید</option>
									<option v-for="option in operationTypeChoices" :key="option.value" :value="option.value">
										{{ option.label }}
									</option>
								</select>
							</div>

							<div class="col-md-6 mb-3">
								<label class="form-label">نوع موتور</label>
								<select v-model="formData.motor_type" class="form-control" required>
									<option value="" disabled>انتخاب کنید</option>
									<option v-for="option in motorTypeChoices" :key="option.value" :value="option.value">
										{{ option.label }}
									</option>
								</select>
							</div>

							<div class="col-md-6 mb-3">
								<label class="form-label">برند موتور</label>
								<input 
									v-model="formData.motor_brand" 
									type="text" 
									class="form-control inputs" 
									required
								/>
							</div>

							<div class="col-md-6 mb-3">
								<label class="form-label">قدرت موتور (کیلووات)</label>
								<input 
									v-model.number="formData.motor_power_kw" 
									type="number" 
									step="0.1"
									class="form-control inputs" 
									min="0"
									required
								/>
							</div>

							<div class="col-md-6 mb-3">
								<label class="form-label">تصویر پلاک موتور</label>
								<input 
									:disabled="true"
									type="file" 
									class="form-control" 
									accept="image/*"
									@change="handleImageUpload($event, 'motor_nameplate_image')"
								/>
							</div>

							<div class="col-md-6 mb-3">
								<label class="form-label">نوع کدگذار موتور</label>
								<select v-model="formData.motor_encoder_type" class="form-control" required>
									<option value="" disabled>انتخاب کنید</option>
									<option v-for="option in motorEncoderTypeChoices" :key="option.value" :value="option.value">
										{{ option.label }}
									</option>
								</select>
							</div>

							<div class="col-md-6 mb-3">
								<label class="form-label">سرعت آسانسور (متر بر ثانیه)</label>
								<input 
									v-model.number="formData.elevator_speed_mps" 
									type="number" 
									step="0.1"
									class="form-control inputs" 
									min="0"
									required
								/>
							</div>

							<div class="col-md-6 mb-3">
								<label class="form-label">برند پنل کنترل</label>
								<input 
									v-model="formData.control_panel_brand" 
									type="text" 
									class="form-control inputs" 
									required
								/>
							</div>

							<div class="col-md-6 mb-3">
								<label class="form-label">سریال پنل کنترل</label>
								<input 
									v-model="formData.control_panel_serial" 
									type="text" 
									class="form-control inputs" 
									required
								/>
							</div>

							<div class="col-md-6 mb-3">
								<label class="form-label">تصویر پنل کنترل</label>
								<input 
								:disabled="true"
									type="file" 
									class="form-control" 
									accept="image/*"
									@change="handleImageUpload($event, 'control_panel_image')"
								/>
							</div>

							<div class="col-md-6 mb-3">
								<label class="form-label">نوع پنل کنترل</label>
								<select v-model="formData.control_panel_type" class="form-control" required>
									<option value="" disabled>انتخاب کنید</option>
									<option v-for="option in controlPanelTypeChoices" :key="option.value" :value="option.value">
										{{ option.label }}
									</option>
								</select>
							</div>

							<div class="col-md-6 mb-3">
								<label class="form-label">برند در</label>
								<input 
									v-model="formData.door_brand" 
									type="text" 
									class="form-control inputs" 
									required
								/>
							</div>

							<div class="col-md-6 mb-3">
								<label class="form-label">تعداد درها</label>
								<select v-model.number="formData.door_count" class="form-control" required>
									<option value="" disabled>انتخاب کنید</option>
									<option v-for="count in doorCountChoices" :key="count" :value="count">
										{{ count }}
									</option>
								</select>
							</div>

							<div v-if="formData.door_count >= 1" class="col-12 mb-3">
								<h6 class="text-secondary">مشخصات در اول</h6>
								<div class="row">
									<div class="col-md-6 mb-3">
										<label class="form-label">نوع در اول</label>
										<select v-model="formData.door1_type" class="form-control" required>
											<option value="" disabled>انتخاب کنید</option>
											<option v-for="option in doorTypeChoices" :key="option.value" :value="option.value">
												{{ option.label }}
											</option>
										</select>
									</div>
									<div class="col-md-6 mb-3">
										<label class="form-label">ولتاژ در اول</label>
										<input 
											v-model="formData.door1_voltage" 
											type="text" 
											class="form-control inputs" 
											required
										/>
									</div>
								</div>
							</div>

							<div v-if="formData.door_count >= 2" class="col-12 mb-3">
								<h6 class="text-secondary">مشخصات در دوم</h6>
								<div class="row">
									<div class="col-md-6 mb-3">
										<label class="form-label">نوع در دوم</label>
										<select v-model="formData.door2_type" class="form-control">
											<option value="" disabled>انتخاب کنید</option>
											<option v-for="option in doorTypeChoices" :key="option.value" :value="option.value">
												{{ option.label }}
											</option>
										</select>
									</div>
									<div class="col-md-6 mb-3">
										<label class="form-label">ولتاژ در دوم</label>
										<input 
											v-model="formData.door2_voltage" 
											type="text" 
											class="form-control inputs" 
										/>
									</div>
								</div>
							</div>

							<div v-if="formData.door_count >= 3" class="col-12 mb-3">
								<h6 class="text-secondary">مشخصات در سوم</h6>
								<div class="row">
									<div class="col-md-6 mb-3">
										<label class="form-label">نوع در سوم</label>
										<select v-model="formData.door3_type" class="form-control">
											<option value="" disabled>انتخاب کنید</option>
											<option v-for="option in doorTypeChoices" :key="option.value" :value="option.value">
												{{ option.label }}
											</option>
										</select>
									</div>
									<div class="col-md-6 mb-3">
										<label class="form-label">ولتاژ در سوم</label>
										<input 
											v-model="formData.door3_voltage" 
											type="text" 
											class="form-control inputs" 
										/>
									</div>
								</div>
							</div>

							<div class="col-md-6 mb-3">
								<label class="form-label">نوع اینورتر</label>
								<input 
									v-model="formData.inverter_type" 
									type="text" 
									class="form-control inputs" 
									required
								/>
							</div>

							<div class="col-md-6 mb-3">
								<label class="form-label">قدرت اینورتر</label>
								<input 
									v-model="formData.inverter_power" 
									type="text" 
									class="form-control inputs" 
									required
								/>
							</div>

							<div class="col-md-6 mb-3">
								<label class="form-label">نوع سیستم کنترل</label>
								<select v-model="formData.control_system_type" class="form-control" required>
									<option value="" disabled>انتخاب کنید</option>
									<option v-for="option in controlSystemTypeChoices" :key="option.value" :value="option.value">
										{{ option.label }}
									</option>
								</select>
							</div>

							<div class="col-md-6 mb-3">
								<label class="form-label">نوع سیستم اضطراری</label>
								<select v-model="formData.emergency_system_type" class="form-control" required>
									<option value="" disabled>انتخاب کنید</option>
									<option v-for="option in emergencySystemTypeChoices" :key="option.value" :value="option.value">
										{{ option.label }}
									</option>
								</select>
							</div>

							<div class="col-md-6 mb-3">
								<label class="form-label">ولتاژ ورودی</label>
								<select v-model="formData.input_voltage" class="form-control" required>
									<option value="" disabled>انتخاب کنید</option>
									<option v-for="option in inputVoltageChoices" :key="option.value" :value="option.value">
										{{ option.label }}
									</option>
								</select>
							</div>

							<div class="col-md-6 mb-3">
								<label class="form-label">حسگر وزن</label>
								<select v-model="formData.weight_sensor" class="form-control" required>
									<option value="" disabled>انتخاب کنید</option>
									<option v-for="option in weightSensorChoices" :key="option.value" :value="option.value">
										{{ option.label }}
									</option>
								</select>
							</div>

							<div class="col-md-6 mb-3">
								<label class="form-label">حالت آتش‌نشانی</label>
								<select v-model="formData.firefighter_mode" class="form-control" required>
									<option value="" disabled>انتخاب کنید</option>
									<option v-for="option in firefighterModeChoices" :key="option.value" :value="option.value">
										{{ option.label }}
									</option>
								</select>
							</div>

							<div class="col-md-6 mb-3">
								<label class="form-label">نوع استاندارد</label>
								<select v-model="formData.standard_type" class="form-control" required>
									<option value="" disabled>انتخاب کنید</option>
									<option v-for="option in standardTypeChoices" :key="option.value" :value="option.value">
										{{ option.label }}
									</option>
								</select>
							</div>

							<div class="col-md-6 mb-3">
								<label class="form-label">نوع ارتباط فراخوان ورودی</label>
								<select v-model="formData.landing_call_comm_type" class="form-control" required>
									<option value="" disabled>انتخاب کنید</option>
									<option v-for="option in landingCallCommTypeChoices" :key="option.value" :value="option.value">
										{{ option.label }}
									</option>
								</select>
							</div>

							<div class="col-12">
								<div class="d-flex justify-content-end mt-4">
									<button 
										type="button" 
										class="btn btn-secondary" 
										@click="resetForm"
									>
										پاک کردن
									</button>
									<button
										:disabled="!isFormValid" 
										type="submit" 
										class="btn btn-primary accept mr-2"
										@click="addElevator"
									>
										<span v-if="loading" class="spinner-border spinner-border-sm"></span>
										ذخیره
									</button>
								</div>
							</div>
						</div>
					</div>
				</div>
			</div>
		</div>
	</div>
</template>

<script>
export default {
	data() {
		return {
			loading: false,
			formData: {
				title: '',
				elevator_type: '',
				usage_type: '',
				cabin_capacity_kg: '',
				stops_count: '',
				operation_type: '',
				motor_type: '',
				motor_brand: '',
				motor_power_kw: '',
				motor_nameplate_image: null,
				motor_encoder_type: '',
				elevator_speed_mps: '',
				control_panel_brand: '',
				control_panel_serial: '',
				control_panel_image: null,
				control_panel_type: '',
				door_brand: '',
				door_count: '',
				door1_type: '',
				door1_voltage: '',
				door2_type: '',
				door2_voltage: '',
				door3_type: '',
				door3_voltage: '',
				inverter_type: '',
				inverter_power: '',
				control_system_type: '',
				emergency_system_type: '',
				input_voltage: '',
				weight_sensor: '',
				firefighter_mode: '',
				standard_type: '',
				landing_call_comm_type: '',
				type: '',
			},
			elevatorTypeChoices: [
				{ value: 'TRACTION', label: 'کششی' },
				{ value: 'HYDRAULIC', label: 'هیدرولیک' }
			],
			usageTypeChoices: [
				{ value: 'RESIDENTIAL', label: 'مسکونی' },
				{ value: 'OFFICE', label: 'اداری' },
				{ value: 'COMMERCIAL', label: 'تجاری' },
				{ value: 'INDUSTRIAL', label: 'صنعتی' }
			],
			operationTypeChoices: [
				{ value: 'SIMPLEX', label: 'سیمپلکس' },
				{ value: 'DUPLEX', label: 'دوپلکس' },
				{ value: 'GROUP', label: 'گروهی' }
			],
			motorTypeChoices: [
				{ value: 'GEARED', label: 'دارای دنده' },
				{ value: 'GEARLESS', label: 'بدون دنده' }
			],
			motorEncoderTypeChoices: [
				{ value: '1024_24V', label: '1024_24v' },
				{ value: '1024_5V', label: '1024_5v' },
				{ value: 'ERN_1387', label: 'ERN_1387' },
				{ value: 'ERN_1313', label: 'ERN_1313' },
				{ value: 'ERN_413', label: 'ERN_413' },
				{ value: 'OTHER', label: 'سایر' }
			],
			controlPanelTypeChoices: [
				{ value: 'MR', label: 'MR' },
				{ value: 'MRL', label: 'MRL' }
			],
			doorCountChoices: [1, 2, 3],
			doorTypeChoices: [
				{ value: 'SWING', label: 'چرخشی' },
				{ value: 'SEMI_AUTO', label: 'نیمه‌اتوماتیک' },
				{ value: 'AUTO', label: 'اتوماتیک' }
			],
			controlSystemTypeChoices: [
				{ value: 'OPEN_LOOP', label: 'حلقه باز' },
				{ value: 'CLOSED_LOOP', label: 'حلقه بسته' }
			],
			emergencySystemTypeChoices: [
				{ value: 'NONE', label: 'هیچ' },
				{ value: 'UPS', label: 'UPS' },
				{ value: 'HDRU', label: 'HDRU' }
			],
			inputVoltageChoices: [
				{ value: 'SINGLE_PHASE', label: 'تک‌فاز' },
				{ value: 'THREE_PHASE', label: 'سه‌فاز' },
				{ value: 'OTHER', label: 'سایر' }
			],
			weightSensorChoices: [
				{ value: 'NONE', label: 'هیچ' },
				{ value: 'EXISTS', label: 'وجود دارد' }
			],
			firefighterModeChoices: [
				{ value: 'INACTIVE', label: 'غیرفعال' },
				{ value: 'MODE1', label: 'مدل1' },
				{ value: 'MODE2', label: 'مدل2' }
			],
			standardTypeChoices: [
				{ value: 'EN81', label: 'EN81' },
				{ value: 'EN81-20', label: 'EN81-20' }
			],
			landingCallCommTypeChoices: [
				{ value: 'SERIAL', label: 'سریال' },
				{ value: 'PARALLEL', label: 'موازی' }
			]
		};
	},
	computed: {
		isFormValid() {
			const requiredFields = [
				'title','type', 'elevator_type', 'usage_type', 'cabin_capacity_kg', 'stops_count',
				'operation_type', 'motor_type', 'motor_brand', 'motor_power_kw',
				'motor_encoder_type', 'elevator_speed_mps', 'control_panel_brand',
				'control_panel_serial', 'control_panel_type', 'door_brand', 'door_count',
				'door1_type', 'door1_voltage', 'inverter_type', 'inverter_power',
				'control_system_type', 'emergency_system_type', 'input_voltage',
				'weight_sensor', 'firefighter_mode', 'standard_type', 'landing_call_comm_type'
			];
			
			return requiredFields.every(field => {
				const value = this.formData[field];
				return value !== '' && value !== null && value !== undefined;
			});
		}
	},
	methods: {
		handleImageUpload(event, fieldName) {
			const file = event.target.files[0];
			if (file) {
				this.formData[fieldName] = file;
			}
		},
		resetForm() {
			Object.keys(this.formData).forEach(key => {
				if (typeof this.formData[key] === 'string') {
					this.formData[key] = '';
				} else if (typeof this.formData[key] === 'number') {
					this.formData[key] = '';
				} else {
					this.formData[key] = null;
				}
			});
		},
		async addElevator() {
			// console.log(this.formData);
			this.loading = true;
			try {
				const formDataToSend = new FormData();
				
				// Add all form fields to FormData
				Object.keys(this.formData).forEach(key => {
					if (this.formData[key] !== null && this.formData[key] !== '') {
						formDataToSend.append(key, this.formData[key]);
					}
				});

				const res = await this.$ApiServiceLayer.post(
					this.$PATH.RELATIVE_PATH.MULTI.ELEVATOR_LIST_CREATE,
					'',
					formDataToSend,
				
				);

				if (res.status === 201) {
					const data = {
						elevator: res.data.id,
						building: this.$route.params.id,
					};
					const response = await this.$ApiServiceLayer.post(
						this.$PATH.RELATIVE_PATH.MULTI.BUILDING_ELEVATOR_LIST_CREATE,
						'',
						data,
					);
					if (response.status === 201) {
						this.$notify({
							group: 'tc',
							type: 'success',
							text: 'آسانسور با موفقیت ثبت شد',
						});
						// this.resetForm();
						
						setTimeout(() => {
							window.close();
						}, 2000);

					}
				}
			} catch (error) {
				this.$notify({
					group: 'tc',
					type: 'error',
					text: 'خطا در ثبت آسانسور',
				});
			} finally {
				this.loading = false;
			}
		},
	},
};
</script>

<style lang="scss" scoped>
.follow-order {
	min-height: 100vh;
	background: #f8f9fa;
	padding: 20px 0;
}

.box {
	background: white;
	border-radius: 12px;
	box-shadow: 0 2px 20px rgba(0, 0, 0, 0.1);
	margin: 24px;
}

.form-container {
	padding: 0;
}

.form-label {
	font-weight: 600;
	color: #333;
	margin-bottom: 8px;
	font-size: 14px;
}

.form-control {
	border: 1px solid #e1e5e9;
	border-radius: 8px;
	// padding: 12px 16px;
	height: 40px;
	font-size: 14px;
	transition: all 0.3s ease;
	background: white;

	&:focus {
		border-color: #357ae1;
		// box-shadow: 0 0 0 3px rgba(53, 122, 225, 0.1);
		outline: none;
	}

	&:disabled {
		background: #f8f9fa;
		opacity: 0.7;
	}
}

.inputs {
	&:hover {
		border-color: #357ae1;
	}
}

.text-primary {
	color: #357ae1 !important;
	font-weight: 700;
}

.text-secondary {
	font-weight: 600;
	margin-top: 20px;
	margin-bottom: 15px;
	padding-bottom: 8px;
	border-bottom: 2px solid #e9ecef;
}

.btn {
	padding: 12px 24px;
	font-weight: 600;
	border-radius: 8px;
	transition: all 0.3s ease;
	border: none;
	font-size: 14px;
	
	&.accept {
		background: #357ae1;
		color: white;
		min-width: 120px;

		&:hover:not(:disabled) {
			background: #2c5aa0;
			transform: translateY(-2px);
		}

		&:disabled {
			background: #357AE1;
			opacity: 0.6;
		}
	}

	&.btn-secondary {
		background: transparent;
		color: #357AE1;
		border: 1px solid #357AE1 !important;

		&:hover {
			background: #5a6268;
			transform: translateY(-2px);
		}
	}
}

.spinner-border-sm {
	width: 1rem;
	height: 1rem;
}

@media (max-width: 768px) {
	.follow-order {
		padding: 10px;
	}
	
	.box {
		margin: 0 10px;
	}
	
	.form-container {
		padding: 0;
	}
	
	.p-4 {
		padding: 20px !important;
	}
	
	.btn {
		width: 100%;
		margin-bottom: 10px;
		
		&.me-2 {
			margin-right: 0 !important;
		}
	}
	
	.d-flex.justify-content-end {
		flex-direction: column-reverse;
		align-items: stretch;
	}
}

@media (max-width: 576px) {
	.col-md-6 {
		margin-bottom: 20px;
	}
	
	.form-control {
		font-size: 16px;
	}
}
</style>
